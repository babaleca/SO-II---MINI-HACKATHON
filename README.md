# O Labirinto dos Processos

Trabalho de Sistemas Operacionais II — PUC Goiás

Uma aplicação que simula vários processos percorrendo um labirinto. Cada processo é um explorador independente, com tarefas próprias, e só consegue encontrar a saída depois de cumprir todas elas. Durante a execução é possível criar, finalizar, suspender e retomar qualquer explorador.

O labirinto é exibido no navegador e atualizado em tempo real.

## Como rodar

É necessário apenas Python 3. O projeto usa só a biblioteca padrão.

Na raiz do projeto:

```bash
python servidor.py
```

Depois abra `http://localhost:8000` no navegador.

Em sistemas onde o comando é `python3`, use `python3 servidor.py`.

Para encerrar, `Ctrl+C` no terminal.

### Sobre suspender e retomar

Esses dois comandos usam os sinais `SIGSTOP` e `SIGCONT`, que existem em Linux e macOS. No Windows é necessário rodar pelo WSL ou usar a biblioteca `psutil` como alternativa.

## Estrutura

| Arquivo | O que faz |
| --- | --- |
| `protocolo.py` | Formato das mensagens trocadas entre os módulos |
| `labirinto.py` | O mapa e as consultas sobre ele |
| `explorador.py` | Comportamento de cada processo filho |
| `coordenador.py` | Criação e controle dos processos |
| `servidor.py` | Servidor HTTP que liga o coordenador à interface |
| `web/` | Interface: HTML, CSS e JavaScript |

Documentação detalhada do módulo explorador em `README-explorador.md`.

## Como funciona

### Criação dos processos

Um processo coordenador (o pai) cria N processos exploradores (os filhos) usando `multiprocessing.Process`. Cada filho recebe seu identificador, a posição inicial e a lista de tarefas que precisa cumprir.

São processos reais, com PID próprio, não threads. Por isso não compartilham memória, e é daí que vem a necessidade de comunicação descrita abaixo.

### Controle dos processos

Pela interface é possível, a qualquer momento:

- **criar** um explorador novo durante a execução
- **finalizar** um explorador
- **suspender** um explorador, com `SIGSTOP`
- **retomar** um explorador suspenso, com `SIGCONT`

O processo suspenso não é destruído. Ele congela exatamente onde estava e volta do mesmo ponto quando recebe o `SIGCONT`.

### Comunicação e sincronização

**Queue.** Cada explorador envia mensagens ao coordenador informando onde está, o que coletou e se conseguiu sair. É por esse canal que o coordenador sabe o que está acontecendo, já que não compartilha memória com os filhos.

**Lock.** As casas marcadas com `~` são corredores estreitos e aceitam um explorador por vez. Quem quer entrar precisa adquirir o Lock, e quem está dentro só o libera ao sair.

### A regra da saída

Cada explorador nasce com dois itens na lista. Se chegar à saída faltando algum, é barrado e continua andando. Só sai quem cumpriu tudo.

## O labirinto

Grid fixo de 17 por 11 casas.

```
#################
#S....#.....#..L#
#.###.#.###.#.#.#
#.#R..~...#.~.#.#
#.#.###.#.#.#.#.#
#...#...#...#..C#
#.#.#.#.###.###.#
#.#...#.....#...#
#.#####.###.#.#.#
#B....~...#...#E#
#################
```

| Símbolo | Significado |
| --- | --- |
| `#` | parede |
| `.` | caminho livre |
| `~` | corredor estreito, protegido por Lock |
| `S` | ponto de partida |
| `E` | saída |
| `L` `R` `C` `B` | itens: Lanterna, Retrato, Chave e Boneca |

## Divisão do trabalho

| Parte | Responsável | Arquivos |
| --- | --- | --- |
| 1. Contratos e mapa | Bárbara Bandarra | `protocolo.py`, `labirinto.py` |
| 2. Interface | Bárbara Bandarra | `web/` |
| 3. Explorador | | `explorador.py` |
| 4. Coordenador e servidor | | `coordenador.py`, `servidor.py` |

O `protocolo.py` foi escrito primeiro justamente para permitir que as outras três partes fossem desenvolvidas em paralelo, cada uma em sua branch, sem depender do término das demais.

## Limitações

O escopo foi mantido simples de propósito, cobrindo os requisitos sem complexidade extra:

- movimento aleatório, sem busca de caminho
- mapa fixo, sem geração procedural
- um único Lock para todos os corredores
- sem tratamento geral de deadlock
