"""
O labirinto: mapa fixo e as perguntas que se faz sobre ele.

Nao sabe nada de processos. So responde "isso e parede?", "o que tem aqui?",
"pra onde da pra ir daqui?".

Coordenadas sao sempre (y, x): y = linha, x = coluna.
"""

PAREDE = "#"
CHAO = "."
CORREDOR = "~"   # so passa um explorador por vez, protegido por Lock
SAIDA = "E"
INICIO = "S"

# itens colecionaveis
ITENS = {
    "L": "Lanterna",
    "C": "Chave",
    "R": "Retrato",
    "B": "Boneca",
}

# 17 colunas x 11 linhas
MAPA = [
    "#################",
    "#S....#.....#..L#",
    "#.###.#.###.#.#.#",
    "#.#R..~...#.~.#.#",
    "#.#.###.#.#.#.#.#",
    "#...#...#...#..C#",
    "#.#.#.#.###.###.#",
    "#.#...#.....#...#",
    "#.#####.###.#.#.#",
    "#B....~...#...#E#",
    "#################",
]

ALTURA = len(MAPA)
LARGURA = len(MAPA[0])

POSICAO_INICIAL = (1, 1)

# quantos exploradores nascem junto com o programa
EXPLORADORES_INICIAIS = 3

# nomes usados na interface, na ordem de criacao
NOMES = ["Vulto", "Bruma", "Cinza", "Traça", "Névoa", "Eco"]


def celula(y, x):
    """O que tem nessa posicao. Fora do mapa conta como parede."""
    if 0 <= y < ALTURA and 0 <= x < LARGURA:
        return MAPA[y][x]
    return PAREDE


def eh_parede(y, x):
    return celula(y, x) == PAREDE


def eh_corredor(y, x):
    return celula(y, x) == CORREDOR


def eh_saida(y, x):
    return celula(y, x) == SAIDA


def item_em(y, x):
    """Devolve o simbolo do item nessa casa, ou None."""
    c = celula(y, x)
    return c if c in ITENS else None


def vizinhos(y, x):
    """Casas para onde da pra andar a partir daqui (cima, baixo, esquerda, direita)."""
    passos = [(y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)]
    return [(ny, nx) for ny, nx in passos if not eh_parede(ny, nx)]


def posicao_saida():
    for y in range(ALTURA):
        for x in range(LARGURA):
            if eh_saida(y, x):
                return (y, x)
    return None


def todos_os_itens():
    """Lista dos simbolos que existem no mapa, na ordem em que aparecem."""
    achados = []
    for linha in MAPA:
        for c in linha:
            if c in ITENS and c not in achados:
                achados.append(c)
    return achados


def checklist_para(indice):
    """
    Monta a checklist do explorador numero `indice` (comecando em 0).
    Cada um recebe 2 itens, girando a lista para dar combinacoes diferentes.
    """
    itens = todos_os_itens()
    a = itens[indice % len(itens)]
    b = itens[(indice + 1) % len(itens)]
    return {a: False, b: False}
