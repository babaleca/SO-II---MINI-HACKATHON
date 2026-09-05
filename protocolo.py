"""
Formatos de mensagem usados por todo o projeto.

Ninguem edita este arquivo sozinho. Se precisar mudar algo, avisa no grupo.

Fluxo:
  explorador  --Queue-->  coordenador  --JSON/HTTP-->  interface
  interface   --HTTP-->   coordenador  --sinais-->     explorador
"""

# status possiveis de um explorador
RODANDO = "rodando"
SUSPENSO = "suspenso"
FINALIZADO = "finalizado"
SAIU = "saiu"

# tipos de mensagem que o explorador manda na Queue
MSG_POSICAO = "posicao"
MSG_ITEM = "item"
MSG_SAIU = "saiu"
MSG_BLOQUEADO = "bloqueado"

# acoes que a interface pode pedir
ACAO_CRIAR = "criar"
ACAO_FINALIZAR = "finalizar"
ACAO_SUSPENDER = "suspender"
ACAO_RETOMAR = "retomar"


# ---------------------------------------------------------------
# mensagens do explorador para o coordenador (Parte 3 usa isso)
# ---------------------------------------------------------------

def msg_posicao(id_exp, y, x):
    """Andou. Manda toda vez que muda de casa."""
    return {"tipo": MSG_POSICAO, "id": id_exp, "pos": [y, x]}


def msg_item(id_exp, simbolo):
    """Pegou um item da checklist."""
    return {"tipo": MSG_ITEM, "id": id_exp, "item": simbolo}


def msg_saiu(id_exp):
    """Chegou na saida com a checklist completa."""
    return {"tipo": MSG_SAIU, "id": id_exp}


def msg_bloqueado(id_exp):
    """Chegou na saida faltando item. Foi barrado."""
    return {"tipo": MSG_BLOQUEADO, "id": id_exp}


# ---------------------------------------------------------------
# estado que o coordenador serve para a interface (Partes 2 e 4)
# ---------------------------------------------------------------

def estado(mapa, exploradores, corredor_ocupado=False):
    """
    Monta o JSON completo que a interface busca a cada 300ms.

    mapa: lista de strings, o labirinto cru
    exploradores: lista de dicts feitos por explorador_estado()
    """
    return {
        "mapa": mapa,
        "exploradores": exploradores,
        "corredor_ocupado": corredor_ocupado,
    }


def explorador_estado(id_exp, nome, y, x, status, checklist):
    """
    Situacao de um explorador.

    checklist: dict simbolo -> True/False. Ex: {"R": True, "C": False}
    """
    return {
        "id": id_exp,
        "nome": nome,
        "pos": [y, x],
        "status": status,
        "checklist": checklist,
        "completo": all(checklist.values()),
    }


# ---------------------------------------------------------------
# comandos da interface para o coordenador (Partes 2 e 4)
# ---------------------------------------------------------------

def comando(acao, id_exp=None):
    """Corpo do POST /comando. id_exp so e usado nas acoes com alvo."""
    return {"acao": acao, "id": id_exp}


# rotas do servidor, para ninguem digitar errado
ROTA_ESTADO = "/estado"
ROTA_COMANDO = "/comando"
PORTA = 8000
