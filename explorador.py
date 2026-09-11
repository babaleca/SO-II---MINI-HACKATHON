"""pt3
 processo explorador e demonstracao independente no terminal.

Integracao com a Parte 4:
    Process(target=explorar, args=(id_exp, checklist, fila, lock_corredor))

Todos os exploradores devem receber a MESMA Queue e o MESMO Lock.
Coordenadas seguem o contrato (y, x). Nao altera o mapa nem o protocolo.
"""

import multiprocessing as mp
import random
import time
from queue import Empty

import labirinto
import protocolo


def explorar(id_exp, checklist, fila, lock_corredor, intervalo=0.3,
             parar=None):
    """Roda no processo filho ate sair ou receber o Event opcional de parada.

    checklist: dicionario {simbolo: bool}, vindo de checklist_para(indice).
    fila: multiprocessing.Queue de mensagens para o coordenador.
    lock_corredor: multiprocessing.Lock compartilhado entre os filhos.
    parar: multiprocessing.Event opcional para encerramento cooperativo.

    SIGSTOP/SIGCONT e a criacao dos processos pertencem ao coordenador.
    Encerramento forcado pode impedir o finally de liberar o Lock; ao
    integrar, prefira o Event para finalizar (retomando antes se suspenso).
    """
    checklist = checklist.copy()  # Cada explorador tem sua propria coleta.
    y, x = labirinto.POSICAO_INICIAL
    possui_lock = False

    def deve_parar():
        return parar is not None and parar.is_set()

    try:
        fila.put(protocolo.msg_posicao(id_exp, y, x))

        while not deve_parar():
            opcoes = labirinto.vizinhos(y, x)
            if not opcoes:
                return
            ny, nx = random.choice(opcoes)
            destino_corredor = labirinto.eh_corredor(ny, nx)

            # Espera ANTES de entrar; timeout permite verificar a parada.
            if destino_corredor and not possui_lock:
                while not deve_parar():
                    if lock_corredor.acquire(timeout=0.1):
                        possui_lock = True
                        break
                if deve_parar():
                    return

            # A saida incompleta e barrada: continua na casa anterior.
            if labirinto.eh_saida(ny, nx) and not all(checklist.values()):
                fila.put(protocolo.msg_bloqueado(id_exp))
            else:
                y, x = ny, nx
                fila.put(protocolo.msg_posicao(id_exp, y, x))

                # Mantem o Lock durante toda a permanencia no corredor.
                if possui_lock and not destino_corredor:
                    lock_corredor.release()
                    possui_lock = False

                item = labirinto.item_em(y, x)
                if item in checklist and not checklist[item]:
                    checklist[item] = True
                    fila.put(protocolo.msg_item(id_exp, item))

                if labirinto.eh_saida(y, x):
                    fila.put(protocolo.msg_saiu(id_exp))
                    return

            if parar is None:
                time.sleep(intervalo)
            else:
                parar.wait(intervalo)
    finally:
        if possui_lock:
            lock_corredor.release()


def demonstrar(duracao=15):
    """Executa tres processos e imprime mensagens, sem servidor ou interface.

    O movimento e aleatorio: nao ha garantia de saida em quinze segundos.
    """
    contexto = mp.get_context("spawn")
    fila = contexto.Queue()
    lock_corredor = contexto.Lock()
    parar = contexto.Event()
    processos = []

    try:
        for indice in range(labirinto.EXPLORADORES_INICIAIS):
            checklist = labirinto.checklist_para(indice)
            processo = contexto.Process(
                target=explorar,
                args=(indice, checklist, fila, lock_corredor, 0.3, parar),
            )
            processo.start()
            processos.append(processo)
            print(f"Explorador {indice}: PID={processo.pid}, {checklist}",
                  flush=True)

        limite = time.monotonic() + duracao
        while time.monotonic() < limite and any(
            processo.is_alive() for processo in processos
        ):
            try:
                print(fila.get(timeout=0.2), flush=True)
            except Empty:
                pass
    except KeyboardInterrupt:
        print("Encerrando a demonstracao...", flush=True)
    finally:
        parar.set()
        # Drena a Queue enquanto os filhos terminam, para nao prender join().
        while any(processo.is_alive() for processo in processos):
            try:
                print(fila.get(timeout=0.2), flush=True)
            except Empty:
                pass
        for processo in processos:
            processo.join()
        while True:
            try:
                print(fila.get_nowait(), flush=True)
            except Empty:
                break
        fila.close()
        fila.join_thread()


if __name__ == "__main__":
    mp.freeze_support()
    demonstrar()
