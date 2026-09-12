import multiprocessing
import os
import queue as fila_vazia
import signal
import sys

try:
    import psutil
except ImportError:
    psutil = None

import explorador
import labirinto
import protocolo

WINDOWS = sys.platform == "win32"


def _parar_processo(pid):
    if WINDOWS:
        psutil.Process(pid).suspend()
    else:
        os.kill(pid, signal.SIGSTOP)


def _seguir_processo(pid):
    if WINDOWS:
        psutil.Process(pid).resume()
    else:
        os.kill(pid, signal.SIGCONT)


class Coordenador:
    def __init__(self):
        self.fila = multiprocessing.Queue()
        self.lock_corredor = multiprocessing.Lock()
        self.processos = {}
        self.eventos_parada = {}
        self.exploradores = {}
        self._proximo_id = 0
        self._proximo_indice_checklist = 0

    def criar_explorador(self):
        id_exp = self._proximo_id
        self._proximo_id += 1

        nome = labirinto.NOMES[id_exp % len(labirinto.NOMES)]
        checklist = labirinto.checklist_para(self._proximo_indice_checklist)
        self._proximo_indice_checklist += 1
        y, x = labirinto.POSICAO_INICIAL

        parar = multiprocessing.Event()
        processo = multiprocessing.Process(
            target=explorador.explorar,
            args=(id_exp, checklist, self.fila, self.lock_corredor),
            kwargs={"parar": parar},
            daemon=True,
        )
        processo.start()

        self.processos[id_exp] = processo
        self.eventos_parada[id_exp] = parar
        self.exploradores[id_exp] = {
            "nome": nome,
            "pos": [y, x],
            "status": protocolo.RODANDO,
            "checklist": checklist,
        }
        return id_exp

    def criar_iniciais(self):
        for _ in range(labirinto.EXPLORADORES_INICIAIS):
            self.criar_explorador()

    def processar_mensagens(self):
        while True:
            try:
                msg = self.fila.get_nowait()
            except fila_vazia.Empty:
                break
            self._aplicar_mensagem(msg)
        self._reaptar_processos()

    def _reaptar_processos(self):
        for processo in self.processos.values():
            processo.is_alive()

    def _aplicar_mensagem(self, msg):
        exp = self.exploradores.get(msg.get("id"))
        if exp is None:
            return

        tipo = msg["tipo"]
        if tipo == protocolo.MSG_POSICAO:
            exp["pos"] = msg["pos"]
        elif tipo == protocolo.MSG_ITEM:
            if msg["item"] in exp["checklist"]:
                exp["checklist"][msg["item"]] = True
        elif tipo == protocolo.MSG_SAIU:
            exp["status"] = protocolo.SAIU
        elif tipo == protocolo.MSG_BLOQUEADO:
            pass

    def finalizar(self, id_exp):
        processo = self.processos.get(id_exp)
        evento = self.eventos_parada.get(id_exp)
        if processo is None or evento is None:
            return
        if not processo.is_alive():
            self.exploradores[id_exp]["status"] = protocolo.FINALIZADO
            return

        if self.exploradores[id_exp]["status"] == protocolo.SUSPENSO:
            _seguir_processo(processo.pid)

        evento.set()
        self.exploradores[id_exp]["status"] = protocolo.FINALIZADO

    def suspender(self, id_exp):
        processo = self.processos.get(id_exp)
        if processo is None or not processo.is_alive():
            return
        _parar_processo(processo.pid)
        self.exploradores[id_exp]["status"] = protocolo.SUSPENSO

    def retomar(self, id_exp):
        processo = self.processos.get(id_exp)
        if processo is None or not processo.is_alive():
            return
        _seguir_processo(processo.pid)
        self.exploradores[id_exp]["status"] = protocolo.RODANDO

    def corredor_esta_ocupado(self):
        livre = self.lock_corredor.acquire(block=False)
        if livre:
            self.lock_corredor.release()
            return False
        return True

    def estado_atual(self):
        self.processar_mensagens()
        lista = [
            protocolo.explorador_estado(
                id_exp, exp["nome"], exp["pos"][0], exp["pos"][1],
                exp["status"], exp["checklist"],
            )
            for id_exp, exp in self.exploradores.items()
        ]
        return protocolo.estado(labirinto.MAPA, lista, self.corredor_esta_ocupado())