# O Labirinto dos Processos — Parte 3: Explorador

Módulo responsável pelo comportamento de cada explorador no trabalho de Sistemas Operacionais II. Cada explorador executa em um processo filho independente, percorre o labirinto aleatoriamente, coleta os itens da sua checklist e tenta alcançar a saída.

## Arquivos necessários

Coloque estes arquivos na mesma pasta:

| Arquivo | Responsabilidade |
| --- | --- |
| `explorador.py` | Movimentação, coleta, acesso ao corredor e mensagens ao coordenador. |
| `labirinto.py` | Mapa, posição inicial, vizinhos válidos e checklists. Fornecido pela parte 1. |
| `protocolo.py` | Formatos das mensagens compartilhados pelo projeto. Fornecido pela parte 1. |

Se os arquivos baixados tiverem ` (1)` no nome, renomeie-os para `labirinto.py` e `protocolo.py`, pois esses são os nomes usados nos imports. A parte 3 utiliza os contratos existentes sem alterar os dois módulos.

## Requisitos e execução

É necessário Python 3. O módulo utiliza apenas a biblioteca padrão, sem instalação de pacotes adicionais.

No terminal, dentro da pasta dos arquivos, execute:

```bash
python explorador.py
```

Em ambientes nos quais o comando do Python 3 é `python3`:

```bash
python3 explorador.py
```

A demonstração cria a quantidade de processos definida em `labirinto.EXPLORADORES_INICIAIS` — atualmente três — e imprime os PIDs, as checklists iniciais e as mensagens recebidas. Depois de aproximadamente 15 segundos, solicita a parada dos processos, consome as mensagens restantes e encerra.

O movimento é aleatório: encontrar todos os itens e sair dentro desses 15 segundos não é garantido. Não é necessário iniciar interface ou servidor para executar esse teste.

Exemplos de mensagens possíveis, que não representam uma sequência completa:

```python
{'tipo': 'posicao', 'id': 0, 'pos': [1, 1]}
{'tipo': 'item', 'id': 0, 'item': 'L'}
{'tipo': 'bloqueado', 'id': 1}
{'tipo': 'saiu', 'id': 0}
```

## Funcionamento do explorador

A função `explorar()` controla um único explorador:

1. Copia a checklist recebida, começa em `POSICAO_INICIAL` e informa sua posição pela fila.
2. Consulta `labirinto.vizinhos(y, x)` e sorteia uma casa válida com `random.choice()`.
3. Se o destino for um corredor `~`, espera adquirir o `Lock` antes de entrar.
4. Se tentar entrar na saída com itens faltando, envia `msg_bloqueado()` e permanece na posição anterior.
5. Quando o movimento é permitido, atualiza a posição e envia `msg_posicao()`.
6. Ao deixar o corredor, libera o `Lock`.
7. Ao pisar em um item pendente da sua checklist, marca-o como coletado e envia `msg_item()`.
8. Ao entrar na saída com a checklist completa, envia `msg_saiu()` e termina a função.
9. Nas demais situações, aguarda o intervalo configurado e repete o ciclo.

As coordenadas seguem sempre a ordem **`(y, x)`**, ou seja, linha e coluna. Nas mensagens, a posição é uma lista `[y, x]`.

A coleta é individual: o item permanece no mapa e pode ser coletado por outros exploradores. Itens que não pertencem à checklist são ignorados, e um item já coletado não gera outra mensagem de coleta.

## Função principal

```python
explorar(id_exp, checklist, fila, lock_corredor, intervalo=0.3, parar=None)
```

| Parâmetro | Uso |
| --- | --- |
| `id_exp` | Identificador do explorador nas mensagens. |
| `checklist` | Dicionário de itens e valores booleanos, por exemplo `{'L': False, 'R': False}`. |
| `fila` | `multiprocessing.Queue` usada para enviar mensagens ao coordenador. |
| `lock_corredor` | `multiprocessing.Lock` compartilhado por todos os exploradores. |
| `intervalo` | Pausa entre tentativas de movimento, em segundos. Padrão: `0.3`. Use um valor não negativo. |
| `parar` | `multiprocessing.Event` opcional para solicitar encerramento cooperativo. |

A função não devolve o estado final ao pai: a comunicação acontece pelas mensagens na `Queue`. Alterar a checklist local do filho não atualiza automaticamente o estado mantido pelo coordenador.

## Mensagens enviadas

Todas as mensagens são construídas pelas funções de `protocolo.py`.

| Função | Conteúdo | Quando é enviada |
| --- | --- | --- |
| `msg_posicao(id_exp, y, x)` | `{'tipo': 'posicao', 'id': id_exp, 'pos': [y, x]}` | Ao iniciar e após cada movimento permitido. |
| `msg_item(id_exp, simbolo)` | `{'tipo': 'item', 'id': id_exp, 'item': simbolo}` | Ao coletar um item pendente da checklist. |
| `msg_bloqueado(id_exp)` | `{'tipo': 'bloqueado', 'id': id_exp}` | Ao tentar entrar na saída sem completar a checklist. |
| `msg_saiu(id_exp)` | `{'tipo': 'saiu', 'id': id_exp}` | Ao entrar na saída com todos os itens exigidos. |

O tipo `bloqueado` indica uma tentativa de saída barrada; não indica espera pelo `Lock`. O encerramento por `Event` não envia `msg_saiu()`, pois não representa uma saída concluída no labirinto.

## Sincronização do corredor

Todos os exploradores devem receber **o mesmo objeto `Lock`**. Criar um `Lock` diferente para cada processo não garante exclusão mútua entre eles.

O explorador adquire o `Lock` antes de entrar em `~` e o mantém durante toda a permanência no corredor, inclusive durante a pausa entre movimentos. Ele o libera depois de mover-se para uma casa que não seja corredor. Como o projeto usa um único `Lock`, todas as casas `~` compartilham a mesma restrição, mesmo estando separadas no mapa.

A tentativa de aquisição usa um timeout de `0.1` segundo para permitir verificar pedidos de parada enquanto o processo espera. O bloco `finally` libera o `Lock` se a função terminar enquanto ainda o possui, desde que o processo consiga executar esse bloco.

## Integração com a parte 4

O coordenador deve criar a fila e o lock compartilhados e iniciar os processos usando `explorar` como `target`. Este trecho mostra a configuração para um explorador; o consumo da fila e o encerramento devem fazer parte do ciclo do coordenador:

```python
import multiprocessing as mp

import labirinto
from explorador import explorar


if __name__ == '__main__':
    contexto = mp.get_context('spawn')
    fila = contexto.Queue()
    lock_corredor = contexto.Lock()

    id_exp = 0
    parar = contexto.Event()
    processo = contexto.Process(
        target=explorar,
        args=(
            id_exp,
            labirinto.checklist_para(id_exp),
            fila,
            lock_corredor,
        ),
        kwargs={'intervalo': 0.3, 'parar': parar},
    )
    processo.start()

    # O ciclo do coordenador deve consumir fila e tratar comandos.
    # Para solicitar a finalização deste explorador: parar.set().
```

Para criar mais exploradores, reutilize `fila` e `lock_corredor`, atribua IDs distintos e guarde as referências aos processos. Use um `Event` por explorador se precisar finalizar cada um individualmente. A demonstração usa um único `Event` porque encerra todos juntos.

Cabe à parte 4 consumir as mensagens, atualizar posições e checklists, manter os status e implementar os comandos da interface. A parte 3 não implementa servidor HTTP nem comandos de suspensão e retomada.

### Suspensão e encerramento

- `SIGSTOP` e `SIGCONT`, previstos no plano para a parte 4, dependem de um ambiente compatível, como Linux. O teste da parte 3 não utiliza esses sinais.
- Se um explorador for suspenso dentro do corredor, manterá o `Lock` enquanto estiver suspenso. Outros exploradores que tentarem entrar precisarão esperar.
- Para o encerramento cooperativo, o coordenador chama `parar.set()`. Se o processo estiver suspenso, também precisa retomá-lo para que consiga verificar o evento e liberar o `Lock`.
- Finalizar à força, por exemplo com `Process.terminate()`, pode impedir a execução do `finally` e deixar o `Lock` adquirido. Essa integração precisa ser considerada por quem implementa o comando de finalizar.
- O coordenador deve continuar consumindo a fila enquanto os filhos encerram, antes de concluir a espera com `join()`. A função `demonstrar()` exemplifica esse cuidado.

## Validações realizadas

Na preparação desta versão, foram verificados:

- Execução de três processos reais, com mensagens recebidas de todos eles e encerramento normal da demonstração.
- Movimentos entre casas vizinhas válidas.
- Coleta dos itens exigidos e preservação da checklist fornecida pelo chamador.
- Saída permitida com a checklist completa.
- Tentativa de saída barrada com item faltando, sem avanço para a saída nem mensagem de sucesso.
- Aquisição e manutenção do `Lock` durante a permanência no corredor e sua liberação ao sair.

As regras foram verificadas também com trajetos controlados, pois a demonstração aleatória curta não garante exercitar todas elas. Esses testes de regras foram executados separadamente e não estão incluídos como uma suíte neste módulo. A integração com o coordenador, os sinais e a interface ainda deve ser validada em conjunto.

## Limites da implementação

O módulo segue o escopo simplificado do plano: movimento aleatório, mapa fixo e um único `Lock`. Não utiliza busca de caminhos nem tratamento geral de deadlock. Exploradores podem compartilhar casas comuns; a exclusão mútua se aplica às casas de corredor `~`.
