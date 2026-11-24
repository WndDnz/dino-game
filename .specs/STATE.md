# STATE

## Decisions

Entradas AD-001 a AD-004 são retroativas: reconstruídas do código e do git log em 2026-11-22 na migração para tlc-spec-driven. A data de cada uma é a do commit que a introduziu.

### AD-001
- **Decision**: As redes neurais são treinadas por neuroevolução (algoritmo genético sobre pesos e bias), não por backpropagation.
- **Reason**: Não existe dataset rotulado de "ação correta" no jogo; a única medida de qualidade é o score que o dino atinge, que serve direto como fitness.
- **Trade-off**: Convergência lenta e ruidosa; `RedeNeural.SGD`/`backprop` ficam como código de estudo sem uso no treino.
- **Scope**: `AGMLP.py`, `DinoGame.train`, `RedeNeural.py`
- **Date**: 2020-12-28
- **Status**: active

### AD-002
- **Decision**: O contrato de entrada/saída da rede é fixo: entrada `(5,1)` = [distância ao cacto, distância ao ptera, altura do ptera, distância cacto→ptera, velocidade]; saída `(2,1)` = [pular, abaixar], cada ação disparada com ativação > 0.99; topologia `(5, 8, 4, 2)` sigmoide.
- **Reason**: Saída one-hot por ação (commit 3975f3f) e o quinto sensor cacto→ptera (e78d439) foram escolhidos para separar as decisões de pular e abaixar.
- **Trade-off**: Qualquer mudança nos sensores, na ordem deles ou na topologia invalida os `.din` salvos.
- **Scope**: `DinoGame.train`, `Dino.getAction`, arquivos `*.din`
- **Date**: 2024-11-18
- **Status**: superseded by AD-005

### AD-003
- **Decision**: O crossover usa BLX-alpha (alpha = 0.1) com um único beta por filho aplicado a todas as camadas; o crossover de dois pontos (`acasala0`) e o BLX elemento a elemento (`acasala2`) ficam como alternativas não usadas.
- **Reason**: O BLX-alpha explora o espaço contínuo dos pesos além do segmento entre os pais, o que o corte de segmentos não faz.
- **Trade-off**: Um beta escalar faz do filho uma interpolação linear dos pais, com menos diversidade que um beta por gene.
- **Scope**: `AGMLP.RNA_AG.acasala`
- **Date**: 2024-11-11
- **Status**: active

### AD-004
- **Decision**: O melhor indivíduo é persistido com `pickle` do objeto `RedeNeural` inteiro em `bestDino.din`.
- **Reason**: Zero código de serialização.
- **Trade-off**: O arquivo depende do nome do módulo e da classe (`RedeNeural.RedeNeural`) e da versão do numpy; renomear ou mover a classe quebra os `.din` existentes.
- **Scope**: `RedeNeural.save_object`/`load_object`, `*.din`
- **Date**: 2020-12-28
- **Status**: active

### AD-005
- **Decision**: O contrato da rede passa a ser: entrada `(5,1)` normalizada = [`l`/largura, `nl`/largura, `na`/altura, `ds`/largura, `s`/20], com `l = nl = 1.0` e `na = ds = 0.0` quando falta o obstáculo; saída `(2,1)` = [pular, abaixar] com limiar 0.5; pesos e bias iniciados em `normal(0, 1)`; topologia `(5, 8, 4, 2)` sigmoide mantida.
- **Reason**: Medição de 2026-11-22: com entradas em pixels e pesos `normal(-10, 10)`, 100% da primeira camada satura, 328 de 350 redes iniciais nunca pulam e a velocidade quase não influencia a decisão. Pergunta ao usuário: "recomendo incluir os dois [inicialização e normalização] e aceitar a perda dos `.din` antigos. Posso reescrever a spec assim?" - resposta: "Pode reescrever a spec."
- **Trade-off**: Os `.din` salvos até aqui (`bestDino.din`, `bestDino_02_11_2024_1339.din`, `bestDino_100_100_261220.din`) carregam mas não jogam: foram treinados com entradas em pixels.
- **Scope**: `DinoGame.train`, `Dino.getAction`, `RedeNeural.__init__`, arquivos `*.din`
- **Date**: 2026-11-22
- **Status**: superseded by AD-006

### AD-006
- **Decision**: O contrato da rede é o de AD-005 com uma troca: pesos iniciados em `normal(0, 4)` e bias em `normal(0, 1)`. Entrada `(5,1)` normalizada = [`l`/largura, `nl`/largura, `na`/altura, `ds`/largura, `s`/20], com `l = nl = 1.0` e `na = ds = 0.0` quando falta o obstáculo; saída `(2,1)` = [pular, abaixar] com limiar 0.5; topologia `(5, 8, 4, 2)` sigmoide.
- **Reason**: Com `normal(0, 1)` só ~8 de 350 redes iniciais mudam a decisão de pular conforme o cacto se aproxima; com pesos de desvio 4 são ~45. Em um treino real (100 dinos, 12 gerações) a média da população foi de 26 a 145 com desvio 4 e ficou entre 21 e 45 com desvio 1. Opção A apresentada ao usuário, resposta: "Aprovo, pode prosseguir."
- **Trade-off**: Pesos maiores saturam mais a sigmoide; a evidência de treino é uma execução por configuração. Redes salvas com AD-005 continuam válidas: o contrato de entrada e saída não mudou.
- **Scope**: `RedeNeural.__init__`, `DinoGame.train`, `Dino.agir`, arquivos `*.din`
- **Date**: 2026-11-22
- **Status**: superseded by AD-007

### AD-007
- **Decision**: Jogo manual, treino e modo assistir usam uma única pista: até 2 cactos na tela, ptera de 46x40 depois de 700 frames, velocidade +1 a cada 700 frames, e todo obstáculo novo nasce a pelo menos 160 px dos que já estão na tela. O contrato da rede é o de AD-006 com uma troca na primeira entrada: `l` mede o cacto mais próximo que ainda não passou pelo dino e vale 1.0 quando todos já passaram.
- **Reason**: O usuário quis assistir a rede na pista do jogo manual ("Vamos tentar usar o jogo manual com até 2 cactos") e treinar nela ("1. Sim, atualize o treino."), para a rede não ser vista numa pista em que nunca treinou. A distância mínima corrige o ptera que nascia em cima de um cacto ("2. Ok.").
- **Trade-off**: Os scores deixam de ser comparáveis com os treinos anteriores (pista de 1 cacto, ptera de 40x40 depois de 600 frames). Redes salvas antes continuam carregando, mas foram treinadas com `l` negativo depois do cacto e nunca viram 2 cactos.
- **Scope**: `DinoGame.py` (`Pista`, `gameplay`, `train`, `sensores`), arquivos `*.din`
- **Date**: 2026-11-22
- **Status**: active

### AD-008
- **Decision**: Cada treino iniciado pela linha de comando grava em uma pasta própria, `treinos/<AAAAMMDD-HHMMSS>_s<semente>/` ou a indicada por `--saida`: `config.json`, `fitness.csv`, `bestDino.din` e `resumo.json`. A raiz do repositório não recebe mais saída de treino, e `--assistir` sem arquivo usa o treino mais recente. O `fitness.csv` tem as colunas `geracao,melhor,media,mediana,desvio,pior,frames,obstaculos_melhor,obstaculos_media,mortes_cacto,mortes_ptera,diversidade` e nenhum valor que dependa do relógio.
- **Reason**: Um treino apagava o anterior e não registrava hiperparâmetros, semente nem versão do código, então treinos não eram comparáveis. Usuário: "1. Concordo 2. no próprio fitness.csv 3. OK".
- **Trade-off**: Muda o cabeçalho do `fitness.csv` fixado em LOG-02 e o padrão de `--assistir` fixado em WATCH-02; CSVs antigos têm 3 colunas. O tempo por geração não é registrado, para o CSV continuar idêntico entre execuções com a mesma semente.
- **Scope**: `autodino.py`, `DinoGame.train`, `registra_geracao`, `graficos.py`, pasta `treinos/`
- **Date**: 2026-11-22
- **Status**: active

### AD-009
- **Decision**: O fitness de um indivíduo é a média do score em um conjunto fixo de pistas de treino (5 por padrão, `--pistas N`; sementes `semente + 1` a `semente + N`), as mesmas em todas as gerações. A melhor rede de cada geração corre em 20 pistas de teste (sementes 900001 a 900020), que nunca entram na seleção, e a média vai para a coluna nova `teste`, no fim do `fitness.csv`. Cada partida termina aos 14000 frames. `melhor`, `media`, `mediana`, `desvio` e `pior` passam a ser estatísticas do fitness; `frames` e as mortes somam as pistas de treino; os obstáculos são a média por pista de cada dino.
- **Reason**: Medição de 2026-11-23: a mesma rede varia de 105 a 518 pontos conforme a pista (desvio 65), então uma pista por geração mede mais a sorte que a rede. Usuário: "Fixas (Recomendado)", "5 (Recomendado)" e, sobre a spec, "Aprova".
- **Trade-off**: O treino fica cerca de 5 vezes mais longo. Muda o cabeçalho e o significado das colunas fixados em AD-008; os scores deixam de ser comparáveis com os treinos de uma pista por geração.
- **Scope**: `DinoGame.train`, `roda_geracao`, `registra_geracao`, `autodino.py`, `graficos.py`
- **Date**: 2026-11-23
- **Status**: active

## Handoff

- **Feature**: `.specs/features/fixed-test-tracks/` - concluída em 2026-11-23, gate final verde (28 provas)
- **Phase / Task**: Execute encerrado: 8/8 tarefas, 7 achados do Verifier fechados
- **Completed**: T1-T8; achados fechados por 6917f3f, a80156f, 4b7bcc7, e619f2c
- **In-progress** (file:line): none
- **Next step**: Push, quando o usuário autorizar. Próxima feature, já aceita pelo usuário: sensores novos (próximo e segundo obstáculo sem distinguir cacto de ptera, estado do próprio dino) e queda rápida ("Queda rápida parece bom e é mecânica do original que não foi reproduzida. Ok, pode entrar."). Topologia só se o platô continuar. Medir o antes com um treino de pistas fixas (coluna `teste`) antes de mudar os sensores.
- **Blockers**: none
- **Uncommitted files**: none
- **Branch**: master (commits locais desta feature, sem push)
- **Notas**: `test_modos.py::test_sem_janela_metade_do_tempo` mede tempo e falha com a máquina ocupada. No treino com janela, as 20 pistas de teste rodam sem tratar eventos: com redes que chegam ao teto, a janela fica sem responder por alguns segundos a cada geração (observação do Verifier, fora dos critérios).
