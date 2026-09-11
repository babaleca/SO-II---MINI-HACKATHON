import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import protocolo
from coordenador import Coordenador

coordenador = Coordenador()


class Handler(BaseHTTPRequestHandler):
    def _cabecalhos(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self):
        if self.path == protocolo.ROTA_ESTADO:
            corpo = json.dumps(coordenador.estado_atual()).encode("utf-8")
            self._cabecalhos(200)
            self.wfile.write(corpo)
        else:
            self._cabecalhos(404)
            self.wfile.write(b'{"erro": "rota desconhecida"}')

    def do_POST(self):
        if self.path != protocolo.ROTA_COMANDO:
            self._cabecalhos(404)
            self.wfile.write(b'{"erro": "rota desconhecida"}')
            return

        tamanho = int(self.headers.get("Content-Length", 0))
        dados = json.loads(self.rfile.read(tamanho) or b"{}")
        acao = dados.get("acao")
        id_exp = dados.get("id")

        if acao == protocolo.ACAO_CRIAR:
            novo_id = coordenador.criar_explorador()
            resposta = {"ok": True, "id": novo_id}
        elif acao == protocolo.ACAO_FINALIZAR:
            coordenador.finalizar(id_exp)
            resposta = {"ok": True}
        elif acao == protocolo.ACAO_SUSPENDER:
            coordenador.suspender(id_exp)
            resposta = {"ok": True}
        elif acao == protocolo.ACAO_RETOMAR:
            coordenador.retomar(id_exp)
            resposta = {"ok": True}
        else:
            self._cabecalhos(400)
            self.wfile.write(b'{"erro": "acao desconhecida"}')
            return

        self._cabecalhos(200)
        self.wfile.write(json.dumps(resposta).encode("utf-8"))

    def do_OPTIONS(self):
        self._cabecalhos(200)

    def log_message(self, formato, *args):
        pass


def main():
    coordenador.criar_iniciais()
    servidor = ThreadingHTTPServer(("localhost", protocolo.PORTA), Handler)
    print(f"Coordenador no ar em http://localhost:{protocolo.PORTA}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()