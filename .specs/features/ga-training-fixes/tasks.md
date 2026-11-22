# GA Training Fixes Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: none - fase Design pulada; as decisões de estrutura estão em "Design inline" abaixo
**Status**: In Progress
**Approved**: 2026-11-22 - user: "1. Aprova. 2. .gitignore"
**Build**: `python -m py_compile AGMLP.py DinoGame.py RedeNeural.py autodino.py`
**Run unit**: `python -m pytest test_ga.py -v`

---

## Design inline

- **AG (`AGMLP.py`)**: `selecao(popRanqueada, n, k=3)` devolve `n` índices vencedores de torneio. `proximaGeracao` passa a ser: ranquear → `copy.deepcopy` das `tamElite` melhores → `N - tamElite` filhos por `acasala(pai1, pai2)` com pais de torneio → mutação só nos filhos → devolve elite + filhos. `grupoDeReproducao`, `acasalaPppulacao` e `mutacaoPopulacao` ficam sem uso e são apagados.
- **Jogo (`DinoGame.py`)**: a lógica presa no laço de `train` sai para três funções testáveis: `sensores(dino, cac, pte, gamespeed)` (função de módulo, devolve o vetor `(5,1)`), `Dino.agir(action)` (limiar e pulo) e `remove_colididos(dinos, obstaculo, ranked)` (função de módulo). `train` só chama essas funções.
- **Registro**: `registra_geracao(ranked, geracao, melhor_score, saida)` em `DinoGame.py` escreve a linha do CSV, salva a rede se bateu o recorde e devolve o novo recorde. `train` ganha os parâmetros `semente_base=0` e `saida="."`.
- **Testes**: um arquivo `test_ga.py` na raiz, que define `SDL_VIDEODRIVER=dummy` e `SDL_AUDIODRIVER=dummy` antes de importar `DinoGame`.

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: none - strong defaults applied. O projeto não tem testes; tipo e comando abaixo são proposta do agente (pytest 9.0.2 já instalado).

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| Rede neural (`RedeNeural.py`) | unit | 1:1 com os critérios da spec | `test_ga.py` | `python -m pytest test_ga.py -v` |
| Algoritmo genético (`AGMLP.py`) | unit | 1:1 com os critérios e casos de borda da spec | `test_ga.py` | `python -m pytest test_ga.py -v` |
| Funções de jogo extraídas (`DinoGame.py`: `sensores`, `Dino.agir`, `remove_colididos`, `registra_geracao`) | unit | 1:1 com os critérios da spec | `test_ga.py` | `python -m pytest test_ga.py -v` |
| Laço de treino (`DinoGame.train`) | integration | Semente por geração e treino interrompido, sem janela | `test_ga.py` | `python -m pytest test_ga.py -v` |
| Commit de base, configuração | none | - (build gate only) | - | build gate only |

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | Depois de tarefas com testes unitários | `python -m pytest test_ga.py -v` |
| Full | Depois de tarefas com teste de integração | `python -m pytest test_ga.py -v` |
| Build | Fim de fase ou tarefa sem teste | `python -m py_compile AGMLP.py DinoGame.py RedeNeural.py autodino.py; python -m pytest test_ga.py -v` |

---

## Execution Plan

Execução estritamente sequencial, T1 a T11. Dependências reais além da ordem: T6 usa a mutação de T4 e o torneio de T5; T8 usa o laço já alterado por T7; T11 usa as funções de T6 a T10.

### Phase 1: Base

```
T1 → T2
```

### Phase 2: Rede e AG

```
T2 → T3 → T4 → T5 → T6
```

### Phase 3: Jogo

```
T6 → T7 → T8 → T9
```

### Phase 4: Registro e integração

```
T9 → T10 → T11
```

---

## Task Breakdown

### T1: Commit de base das correções pendentes

**What**: Um commit com as alterações não commitadas de `AGMLP.py`, `DinoGame.py`, `RedeNeural.py`, `autodino.py` e `teste.py` (remoção das linhas duplicadas que deixam o HEAD com erro de sintaxe), mais `.specs/` e a linha `graphify-out/` no `.gitignore`.
**Where**: `.gitignore`
**Depends on**: None
**Requirement**: nenhum - pré-requisito para commits atômicos

**Done when**:

- [x] `git status --short` não lista os cinco arquivos `.py`
- [x] Build passa: `python -m py_compile AGMLP.py DinoGame.py RedeNeural.py autodino.py`

**Tests**: none
**Gate**: build

**Commit**: `fix: remove duplicated lines that broke syntax`

---

### T2: Arquivo de testes sem janela

**What**: Criar `test_ga.py` que define os drivers SDL `dummy`, importa `RedeNeural`, `AGMLP` e `DinoGame`, e tem um teste que confirma a importação sem abrir janela.
**Where**: `test_ga.py`
**Depends on**: T1
**Requirement**: meta "A lógica do AG e da rede roda em teste automatizado sem abrir janela"

**Done when**:

- [x] `test_importa_sem_janela` passa
- [x] Gate check passes: `python -m pytest test_ga.py -v`
- [x] Test count: 1 test passes

**Tests**: unit
**Gate**: quick

**Commit**: `test: add headless test file`

---

### T3: Inicialização normal(0, 1)

**What**: `RedeNeural.__init__` sorteia pesos e bias com `np.random.normal(0, 1, ...)`.
**Where**: `RedeNeural.py`
**Depends on**: T2
**Requirement**: INIT-01

**Done when**:

- [x] `test_init_normal_0_1`: com semente fixa, 350 redes `(5,8,4,2)` têm média dos pesos entre −0.05 e 0.05 e desvio entre 0.95 e 1.05; o mesmo para os bias com tolerância 0.1
- [x] Gate check passes: `python -m pytest test_ga.py -v`
- [x] Test count: 2 tests pass

**Tests**: unit
**Gate**: quick

**Commit**: `fix(rede): initialize weights and biases with normal(0, 1)`

---

### T4: Mutação gaussiana aditiva

**What**: `aplicaMutacao(individuo, taxaMutacao, sigma=0.5)` soma `N(0, sigma)` a cada gene com probabilidade `taxaMutacao`.
**Where**: `AGMLP.py`
**Depends on**: T3
**Requirement**: MUT-01, MUT-02, MUT-03

**Done when**:

- [x] `test_mutacao_taxa_1_altera_todos`: todos os pesos e bias diferem do original
- [x] `test_mutacao_taxa_0_nao_altera`: rede idêntica ao original
- [x] `test_mutacao_delta_normal_0_05`: em 1000 genes ou mais com taxa 1.0, média dos deltas entre −0.1 e 0.1, desvio entre 0.4 e 0.6, e há deltas dos dois sinais
- [x] Gate check passes: `python -m pytest test_ga.py -v`
- [x] Test count: 5 tests pass

**Tests**: unit
**Gate**: quick

**Commit**: `fix(ag): additive gaussian mutation`

---

### T5: Torneio de 3

**What**: `selecao(popRanqueada, n, k=3)` devolve `n` índices, cada um o de maior score entre `min(k, len(popRanqueada))` sorteados.
**Where**: `AGMLP.py`
**Depends on**: T4
**Requirement**: AGT-04, caso de borda "menos de 3 indivíduos"

**Done when**:

- [x] `test_torneio_de_3`: com 100 scores distintos e 5000 sorteios, a posição média do vencedor fica entre 0.72 e 0.78 da escala (valor esperado do máximo de 3 = 0.75)
- [x] `test_torneio_populacao_menor_que_3`: com 2 indivíduos, todo vencedor é o de maior score
- [x] Gate check passes: `python -m pytest test_ga.py -v`
- [x] Test count: 7 tests pass

**Tests**: unit
**Gate**: quick

**Commit**: `fix(ag): fixed-size tournament selection`

---

### T6: Próxima geração com elite intacta

**What**: `proximaGeracao` devolve exatamente N redes: cópias profundas das `tamElite` melhores, sem mutação, mais `N - tamElite` filhos mutados; apagar `grupoDeReproducao`, `acasalaPppulacao` e `mutacaoPopulacao`.
**Where**: `AGMLP.py`
**Depends on**: T5
**Reuses**: `acasala`, `ranquearIndividuos`
**Requirement**: AGT-01, AGT-02, AGT-03, caso de borda "elite 0"

**Done when**:

- [x] `test_proxima_geracao_devolve_n`: 50 pares de entrada, 50 redes de saída
- [x] `test_elite_identica`: com `elite=0.1` e N=50, as 5 redes de maior score aparecem na saída com pesos e bias idênticos, em objetos distintos dos de entrada
- [x] `test_entrada_inalterada`: pesos e bias das 50 redes de entrada iguais antes e depois
- [x] `test_sem_elite_gera_n_filhos`: com `elite=0.01` e N=50 (`tamElite` = 0), saída com 50 redes
- [x] Gate check passes: `python -m pytest test_ga.py -v`
- [x] Test count: 11 tests pass

**Tests**: unit
**Gate**: quick

**Commit**: `fix(ag): exact population size and untouched elite`

---

### T7: Sensores normalizados por dino

**What**: Função `sensores(dino, cac, pte, gamespeed)` que devolve o vetor `(5,1)` da spec; `train` a chama para cada dino vivo.
**Where**: `DinoGame.py`
**Depends on**: T6
**Requirement**: SENS-01, SENS-02, SENS-03, SENS-05

**Done when**:

- [x] `test_sensores_normalizados`: com cacto e ptera em posições conhecidas, `l`, `nl`, `ds` = pixels / 600, `na` = pixels / 150, `s` = velocidade / 20
- [x] `test_sensor_sem_cacto`: `l` = 1.0
- [x] `test_sensor_sem_ptera`: `nl` = 1.0, `na` = 0.0, `ds` = 0.0
- [x] `test_sensores_do_proprio_dino`: dois dinos com `rect.right` diferentes recebem `l` diferentes para o mesmo cacto
- [x] Gate check passes: `python -m pytest test_ga.py -v`
- [x] Test count: 15 tests pass

**Tests**: unit
**Gate**: quick

**Commit**: `fix(game): normalized per-dino sensors`

---

### T8: Ação com limiar 0.5 e pulo sem áudio

**What**: Método `Dino.agir(action)`: saída > 0.5 dispara a ação; o pulo define `movement[1] = -jumpSpeed` fora do teste do mixer; `train` o chama.
**Where**: `DinoGame.py`
**Depends on**: T7
**Requirement**: SENS-04, FIT-02

**Done when**:

- [x] `test_limiar_05`: ação `[0.51, 0.49]` faz pular e não abaixar; `[0.49, 0.51]` faz abaixar e não pular
- [x] `test_pulo_sem_mixer`: depois de `pygame.mixer.quit()`, dino no chão com ação de pulo fica com `movement[1] == -jumpSpeed`
- [x] Gate check passes: `python -m pytest test_ga.py -v`
- [x] Test count: 17 tests pass

**Tests**: unit
**Gate**: quick

**Commit**: `fix(game): action threshold 0.5 and jump independent of audio`

---

### T9: Remoção de colididos no mesmo frame

**What**: Função `remove_colididos(dinos, obstaculo, ranked)` que tira da lista todos os dinos que colidem com o obstáculo e acrescenta `(score, rede)` de cada um a `ranked`; `train` a usa para cactos e pteras.
**Where**: `DinoGame.py`
**Depends on**: T8
**Requirement**: FIT-01

**Done when**:

- [x] `test_colisoes_mesmo_frame`: 10 dinos sobre um cacto; uma chamada deixa a lista vazia e `ranked` com 10 entradas, uma por rede
- [x] Gate check passes: `python -m pytest test_ga.py -v`
- [x] Test count: 18 tests pass

**Tests**: unit
**Gate**: quick

**Commit**: `fix(game): remove all colliding dinos in the same frame`

---

### T10: Registro da geração

**What**: Função `registra_geracao(ranked, geracao, melhor_score, saida)` que acrescenta `geracao,melhor,media` a `fitness.csv`, salva a rede em `bestDino.din` quando o melhor da geração supera `melhor_score`, e devolve o novo recorde.
**Where**: `DinoGame.py`
**Depends on**: T9
**Reuses**: `RedeNeural.save_object`
**Requirement**: LOG-02, LOG-03

**Done when**:

- [x] `test_csv_linha_por_geracao`: duas chamadas em diretório temporário deixam cabeçalho e 2 linhas com os valores esperados
- [x] `test_salva_melhor_de_todos`: geração com recorde grava `bestDino.din` com a rede de maior score; geração seguinte com score menor não altera o arquivo
- [x] Gate check passes: `python -m pytest test_ga.py -v`
- [x] Test count: 20 tests pass

**Tests**: unit
**Gate**: quick

**Commit**: `feat(game): per-generation fitness log and best-ever checkpoint`

---

### T11: Treino com semente e registro

**What**: `train(..., semente_base=0, saida=".")` chama `random.seed(semente_base + geração)` antes do primeiro obstáculo, chama `registra_geracao` ao fim de cada geração, recria `fitness.csv` no início do treino, usa `taxaMutacao=0.05` e deixa de salvar só no fim.
**Where**: `DinoGame.py`
**Depends on**: T10
**Reuses**: `sensores`, `Dino.agir`, `remove_colididos` (T7-T9), `proximaGeracao` (T6)
**Requirement**: LOG-01, caso de borda "treino encerrado antes da última geração"

**Done when**:

- [ ] `test_semente_por_geracao`: dois treinos sem janela (N=10, 2 gerações, mesma `semente_base`, `np.random.seed` igual) produzem `fitness.csv` idênticos
- [ ] `test_treino_interrompido_mantem_melhor`: treino de 3 gerações interrompido depois da primeira deixa `bestDino.din` com a melhor rede da geração 1
- [ ] Gate check passes: `python -m py_compile AGMLP.py DinoGame.py RedeNeural.py autodino.py; python -m pytest test_ga.py -v`
- [ ] Test count: 22 tests pass, em menos de 10 s

**Tests**: integration
**Gate**: full

**Commit**: `feat(game): seeded generations and logging wired into train`

---

## Checks

**C1** - Pesos e bias novos seguem normal de média 0 e desvio 1 (INIT-01, AC 1)
Proof: run unit | test_ga.py::test_init_normal_0_1 PASSED

**C2** - `l`, `nl`, `ds` saem divididos por 600, `na` por 150 e `s` por 20 (SENS-01, AC 2)
Proof: run unit | test_ga.py::test_sensores_normalizados PASSED

**C3** - Sem cacto, `l` = 1.0 (SENS-02, AC 3)
Proof: run unit | test_ga.py::test_sensor_sem_cacto PASSED

**C4** - Sem ptera, `nl` = 1.0, `na` = 0.0 e `ds` = 0.0 (SENS-03, AC 4)
Proof: run unit | test_ga.py::test_sensor_sem_ptera PASSED

**C5** - Saída maior que 0.5 dispara a ação; 0.49 não dispara (SENS-04, AC 5)
Proof: run unit | test_ga.py::test_limiar_05 PASSED

**C6** - As distâncias saem do `rect` do dino avaliado (SENS-05, AC 6)
Proof: run unit | test_ga.py::test_sensores_do_proprio_dino PASSED

**C7** - `proximaGeracao` com 50 pares devolve 50 redes (AGT-01, AC 1)
Proof: run unit | test_ga.py::test_proxima_geracao_devolve_n PASSED

**C8** - As 5 redes de maior score reaparecem com pesos e bias idênticos (AGT-02, AC 2)
Proof: run unit | test_ga.py::test_elite_identica PASSED

**C9** - As redes de entrada ficam inalteradas (AGT-03, AC 3)
Proof: run unit | test_ga.py::test_entrada_inalterada PASSED

**C10** - Cada pai é o melhor de 3 sorteados: posição média 0.75 (AGT-04, AC 4)
Proof: run unit | test_ga.py::test_torneio_de_3 PASSED

**C11** - Taxa 1.0 altera todos os pesos e bias (MUT-01, AC 5)
Proof: run unit | test_ga.py::test_mutacao_taxa_1_altera_todos PASSED

**C12** - Taxa 0.0 não altera a rede (MUT-02, AC 6)
Proof: run unit | test_ga.py::test_mutacao_taxa_0_nao_altera PASSED

**C13** - O valor somado tem média 0 e desvio 0.5 (MUT-03, AC 7)
Proof: run unit | test_ga.py::test_mutacao_delta_normal_0_05 PASSED

**C14** - 10 dinos colididos no mesmo frame: 10 registros e lista vazia (FIT-01, AC 1)
Proof: run unit | test_ga.py::test_colisoes_mesmo_frame PASSED

**C15** - Sem mixer, o pulo define `movement[1] = -jumpSpeed` (FIT-02, AC 2)
Proof: run unit | test_ga.py::test_pulo_sem_mixer PASSED

**C16** - Mesma semente, mesmo `fitness.csv` em dois treinos (LOG-01, AC 1)
Proof: run unit | test_ga.py::test_semente_por_geracao PASSED

**C17** - Cada geração acrescenta uma linha `geracao,melhor,media` (LOG-02, AC 2)
Proof: run unit | test_ga.py::test_csv_linha_por_geracao PASSED

**C18** - Só um recorde regrava `bestDino.din` (LOG-03, AC 3)
Proof: run unit | test_ga.py::test_salva_melhor_de_todos PASSED

**C19** - Com `tamElite` = 0 saem N filhos (Edge Case 1)
Proof: run unit | test_ga.py::test_sem_elite_gera_n_filhos PASSED

**C20** - Com 2 indivíduos o torneio usa todos (Edge Case 2)
Proof: run unit | test_ga.py::test_torneio_populacao_menor_que_3 PASSED

**C21** - Treino interrompido deixa a melhor rede das gerações concluídas (Edge Case 3)
Proof: run unit | test_ga.py::test_treino_interrompido_mantem_melhor PASSED

---

## Handoff

**Settled mid-build:** 2026-11-22 - `graphify-out/` vai para o `.gitignore`, não para o commit de base (usuário: "2. .gitignore"). Execução inline, sem sub-agentes: oferta feita junto com o plano ("executo as 11 tarefas nesta sessão, sem sub-agentes"), usuário: "1. Aprova."
**Dispatched:** none
**Walked:** none - a feature não tem tela nova

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4

Phase 1:  T1 → T2
Phase 2:  T2 → T3 → T4 → T5 → T6
Phase 3:  T6 → T7 → T8 → T9
Phase 4:  T9 → T10 → T11
```

11 tarefas: passa do limite de ~8 de um lote. No Execute, a oferta de sub-agentes vem antes da primeira tarefa.

---

## Task Granularity Check

| Task | Scope | Status |
| ---- | ----- | ------ |
| T1: commit de base | 1 commit, nenhum arquivo editado | ✅ Granular |
| T2: arquivo de testes | 1 arquivo | ✅ Granular |
| T3: inicialização | 1 função | ✅ Granular |
| T4: mutação | 1 função | ✅ Granular |
| T5: torneio | 1 função | ✅ Granular |
| T6: próxima geração | 1 função + remoção de 3 funções que ela deixa sem uso | ⚠️ OK, coeso |
| T7: sensores | 1 função + chamada em `train` | ✅ Granular |
| T8: ação | 1 método + chamada em `train` | ✅ Granular |
| T9: colididos | 1 função + chamada em `train` | ✅ Granular |
| T10: registro | 1 função | ✅ Granular |
| T11: treino | 1 função (`train`) | ✅ Granular |

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| ---- | ---------------------- | ------------- | ------ |
| T1 | None | - | ✅ Match |
| T2 | T1 | T1 → T2 | ✅ Match |
| T3 | T2 | T2 → T3 | ✅ Match |
| T4 | T3 | T3 → T4 | ✅ Match |
| T5 | T4 | T4 → T5 | ✅ Match |
| T6 | T5 | T5 → T6 | ✅ Match |
| T7 | T6 | T6 → T7 | ✅ Match |
| T8 | T7 | T7 → T8 | ✅ Match |
| T9 | T8 | T8 → T9 | ✅ Match |
| T10 | T9 | T9 → T10 | ✅ Match |
| T11 | T10 | T10 → T11 | ✅ Match |

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| ---- | --------------------------- | --------------- | --------- | ------ |
| T1 | Commit de base | none | none | ✅ OK |
| T2 | Arquivo de testes | unit | unit | ✅ OK |
| T3 | Rede neural | unit | unit | ✅ OK |
| T4 | Algoritmo genético | unit | unit | ✅ OK |
| T5 | Algoritmo genético | unit | unit | ✅ OK |
| T6 | Algoritmo genético | unit | unit | ✅ OK |
| T7 | Funções de jogo extraídas | unit | unit | ✅ OK |
| T8 | Funções de jogo extraídas | unit | unit | ✅ OK |
| T9 | Funções de jogo extraídas | unit | unit | ✅ OK |
| T10 | Funções de jogo extraídas | unit | unit | ✅ OK |
| T11 | Laço de treino | integration | integration | ✅ OK |
