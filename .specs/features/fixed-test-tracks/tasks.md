# Fixed Test Tracks Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: none - fase Design pulada; as decisões de estrutura estão em "Design inline" abaixo
**Status**: In Progress
**Approved**: 2026-11-23 - user: "Aprovado, pode aplicar."
**Build**: `python -m py_compile AGMLP.py DinoGame.py RedeNeural.py autodino.py graficos.py simula_pista.py`
**Run unit**: `python -m pytest test_ga.py test_modos.py test_registro.py test_pistas.py -v`

---

## Design inline

- **Constantes** em `DinoGame.py`: `PISTAS = 5`, `SEMENTES_TESTE = range(900001, 900021)`, `LIMITE_FRAMES = 14000`. O `config.json` lê delas.
- **Uma pista**: `roda_geracao` continua simulando uma pista e devolvendo `[(score, rede)]`; só ganha o teto de frames.
- **Várias pistas**: `avalia(redes, sementes, janela)` é o único lugar que semeia `random` para uma pista e agrega scores e estatísticas. O treino a usa duas vezes por geração: população nas pistas de treino, melhor rede nas de teste (sempre sem janela).
- **Ordem do resultado**: `avalia` devolve na ordem da população, então o desempate do melhor é sempre o de menor índice.
- **Registro**: `registra_geracao` ganha o parâmetro `teste` e a 13ª coluna; as outras colunas saem do `ranked` (agora fitness) e das estatísticas agregadas, sem mudar de nome.
- **Reprodutibilidade**: as pistas usam só `random`; a população, o crossover e a mutação usam só `numpy.random`. Rodar o teste entre gerações não muda a sequência do numpy.
- **Testes**: arquivo novo `test_pistas.py` na raiz, no padrão dos outros três (driver SDL `dummy`). Os testes antigos que não tratam de pistas passam `pistas=1` quando isso só serve para não ficarem mais lentos.

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: none - strong defaults applied. Padrão existente: `test_ga.py`, `test_modos.py` e `test_registro.py` na raiz, pytest, driver SDL `dummy`.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| Laço de treino (`DinoGame.py`: `roda_geracao`, `avalia`, `train`, `registra_geracao`) | integration | 1:1 com os critérios e casos de borda da spec, rodando o laço de verdade com driver `dummy` | `test_pistas.py` | `python -m pytest test_ga.py test_modos.py test_registro.py test_pistas.py -v` |
| Linha de comando (`autodino.py`) | integration | A opção nova: caminho normal, padrão e valores inválidos | `test_pistas.py` | `python -m pytest test_ga.py test_modos.py test_registro.py test_pistas.py -v` |
| Gráficos (`graficos.py`) | unit | 1:1 com os critérios da spec, conferindo os dados de cada figura | `test_pistas.py` | `python -m pytest test_ga.py test_modos.py test_registro.py test_pistas.py -v` |
| Documentação e ferramenta de investigação (`README.md`, `simula_pista.py`) | none | - (build gate only) | - | build gate only |

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | Depois de tarefas com testes unitários | `python -m pytest test_ga.py test_modos.py test_registro.py test_pistas.py -v` |
| Full | Depois de tarefas com testes de integração | `python -m pytest test_ga.py test_modos.py test_registro.py test_pistas.py -v` |
| Build | Fim de fase ou tarefa sem teste | `python -m py_compile AGMLP.py DinoGame.py RedeNeural.py autodino.py graficos.py simula_pista.py; python -m pytest test_ga.py test_modos.py test_registro.py test_pistas.py -v` |

---

## Execution Plan

Execução estritamente sequencial, T1 a T8.

### Phase 1: Treino

```
T1 → T2 → T3 → T4 → T5
```

### Phase 2: Gráficos e documentação

```
T5 → T6 → T7 → T8
```

---

## Task Breakdown

### T1: Teto de frames por partida

**What**: `roda_geracao` termina a partida no frame `LIMITE_FRAMES` (14000) e devolve os dinos ainda vivos com o score que tinham; eles não contam como morte.
**Where**: `DinoGame.py`
**Depends on**: None
**Reuses**: `roda_geracao`, `Dino.score`
**Requirement**: FIT-06

**Done when**:

- [x] `test_teto_de_frames`: com `LIMITE_FRAMES` trocado para 70 e uma pista sem obstáculos, a partida dura 70 frames, os 3 dinos voltam em `ranked` com score 10 e `mortes_cacto + mortes_ptera` é 0; com o teto em 71 dura 71 frames; um dino que morre antes do teto mantém o score da morte
- [x] Gate check passes: `python -m pytest test_ga.py test_modos.py test_registro.py test_pistas.py -v`
- [x] Test count: os 104 testes anteriores + 1 de `test_pistas.py` passam (105)

**Tests**: integration
**Gate**: full

**Commit**: `feat(train): frame cap per track`

---

### T2: Avaliação em várias pistas

**What**: Método `avalia(redes, sementes, janela)`: semeia `random` com cada semente, roda a população na pista e devolve `[(fitness, rede)]` na ordem da população, com fitness = média dos scores; deixa em `self.estatisticas` a soma de `frames` e das mortes e, em `obstaculos`, a média por pista de cada dino. Devolve `None` se a janela foi fechada.
**Where**: `DinoGame.py`
**Depends on**: T1
**Reuses**: `roda_geracao`, `self.estatisticas` (AD-008)
**Requirement**: FIT-01, FIT-02, FIT-08, FIT-09, TST-09

**Done when**:

- [ ] `test_populacao_corre_em_cada_pista_de_treino`: com sementes (8, 9, 10), `roda_geracao` é chamada 3 vezes, cada uma com as 4 redes e com `random` recém-semeado em 8, 9 e 10
- [ ] `test_fitness_e_a_media_das_pistas`: com scores por pista fixados em (10, 20, 60) e (30, 30, 30) para duas redes, os fitness são 30.0 e 30.0; com (10, 20, 61), 30.333...; conferido também contra a pista real, rodando cada pista em separado
- [ ] `test_frames_e_mortes_somam_as_pistas`: `frames`, `mortes_cacto` e `mortes_ptera` são a soma dos valores de cada pista rodada em separado
- [ ] `test_obstaculos_media_por_pista`: um dino que venceu 2, 4 e 9 obstáculos nas 3 pistas tem 5.0 em `obstaculos`, na posição dele na população
- [ ] `test_empate_no_melhor_e_reproduzivel`: com duas redes idênticas na população, `max` sobre o resultado devolve a de menor índice em duas execuções seguidas
- [ ] Gate check passes: `python -m pytest test_ga.py test_modos.py test_registro.py test_pistas.py -v`
- [ ] Test count: os 105 testes anteriores + 5 de `test_pistas.py` passam (110)

**Tests**: integration
**Gate**: full

**Commit**: `feat(train): evaluate a population on several tracks`

---

### T3: Treino com pistas fixas

**What**: `train` ganha `pistas=PISTAS` (5): toda geração é avaliada por `avalia` nas sementes `semente_base + 1` a `semente_base + pistas`; o registro e o recorde usam o fitness; `config.json` ganha `pistas`, `pistas_teste` e `limite_frames`. Os testes existentes que fixam uma pista por geração são atualizados.
**Where**: `DinoGame.py`
**Depends on**: T2
**Reuses**: `avalia` (T2), `registra_geracao`, `config`
**Requirement**: FIT-03, FIT-07, FIT-10, FIT-11, FIT-12, FIT-13

**Done when**:

- [ ] `test_mesmas_pistas_em_todas_as_geracoes`: em 3 gerações com `semente_base=7` e `pistas=2`, as sementes usadas são (8, 9) em cada geração
- [ ] `test_estatisticas_sobre_o_fitness`: com fitness fixados em (10.5, 20.0, 60.0, 30.0), a linha traz melhor 60.0, média 30.125, mediana 25.0, pior 10.5 e o desvio populacional desses valores
- [ ] `test_recorde_pelo_fitness`: `bestDino.din` é regravado na geração em que o maior fitness passa do recorde e fica intacto quando o maior fitness é igual ou menor
- [ ] `test_config_traz_pistas`: `config.json` traz `pistas` 3 quando o treino usa 3, `pistas_teste` 20 e `limite_frames` 14000
- [ ] `test_uma_pista_so`: com `pistas=1` e `semente_base=7`, a única semente usada em todas as gerações é 8
- [ ] `test_janela_fechada_nao_registra_geracao`: fechar a janela na 2ª pista da geração 2 encerra o treino com o `fitness.csv` contendo só a geração 1
- [ ] `test_semente_por_geracao` (`test_ga.py`) e o teste de mesma pista entre assistir e treino (`test_modos.py`) atualizados para pistas fixas; nenhum teste removido
- [ ] Gate check passes: `python -m pytest test_ga.py test_modos.py test_registro.py test_pistas.py -v`
- [ ] Test count: os 110 testes anteriores + 6 de `test_pistas.py` passam (116)

**Tests**: integration
**Gate**: full

**Commit**: `feat(train): fitness is the mean over fixed tracks`

---

### T4: Pistas de teste

**What**: Depois de cada geração, `train` roda a rede de maior fitness nas 20 pistas de `SEMENTES_TESTE` (900001 a 900020), sem janela, e `registra_geracao` grava a média na coluna nova `teste`; `resumo.json` ganha `teste_do_melhor` e a linha impressa ganha `teste=`.
**Where**: `DinoGame.py`
**Depends on**: T3
**Reuses**: `avalia` (T2), `COLUNAS`, `registra_geracao`
**Requirement**: TST-01, TST-02, TST-03, TST-04, TST-05, TST-06, TST-07, TST-08

**Done when**:

- [ ] `test_melhor_corre_nas_pistas_de_teste`: a cada geração, `avalia` é chamada com uma única rede, a de maior fitness, e as sementes 900001 a 900020
- [ ] `test_coluna_teste_e_a_media`: com scores de teste fixados, `teste` é a média deles; conferido também contra a pista real para a rede salva em `bestDino.din`
- [ ] `test_cabecalho_com_teste`: a primeira linha do `fitness.csv` é a de 13 colunas da spec
- [ ] `test_selecao_ignora_o_teste`: trocar os scores de teste por outros valores não muda nenhuma outra coluna do `fitness.csv` nem a rede salva
- [ ] `test_pistas_de_teste_independem_das_opcoes`: treinos com `semente_base` 3 e 11 e `pistas` 1 e 3 usam as mesmas 20 sementes de teste
- [ ] `test_resumo_traz_teste_do_melhor`: `teste_do_melhor` é o `teste` da linha da geração `geracao_do_melhor`
- [ ] `test_linha_impressa_com_teste`: sem janela, a linha de cada geração é `Geração <g>: melhor=<melhor> media=<media> teste=<teste>` com os valores do CSV
- [ ] `test_csv_igual_com_e_sem_janela_com_pistas`: 10 dinos, 3 gerações, 2 pistas, com e sem janela: os dois `fitness.csv` são idênticos e têm 13 colunas
- [ ] Asserções de cabeçalho e de linha impressa dos testes existentes atualizadas para o formato novo
- [ ] Gate check passes: `python -m pytest test_ga.py test_modos.py test_registro.py test_pistas.py -v`
- [ ] Test count: os 116 testes anteriores + 8 de `test_pistas.py` passam (124)

**Tests**: integration
**Gate**: full

**Commit**: `feat(train): held-out test tracks and the teste column`

---

### T5: Opção --pistas

**What**: `autodino.py` aceita `--pistas N` (inteiro ≥ 1) e o repassa a `train`.
**Where**: `autodino.py`
**Depends on**: T4
**Reuses**: `_um_ou_mais`, `main`
**Requirement**: FIT-04, FIT-05

**Done when**:

- [ ] `test_opcao_pistas`: `--pistas 3` chega a `train` como `pistas=3` com e sem janela; sem a opção, o `config.json` do treino traz `pistas` 5
- [ ] `test_pistas_invalido_codigo_2`: `--pistas 0`, `--pistas -1` e `--pistas 2.5` encerram com código 2 sem criar pasta em `treinos/`
- [ ] Gate check passes: `python -m pytest test_ga.py test_modos.py test_registro.py test_pistas.py -v`
- [ ] Test count: os 124 testes anteriores + 2 de `test_pistas.py` passam (126)

**Tests**: integration
**Gate**: full

**Commit**: `feat(cli): --pistas option`

---

### T6: Curva de teste no gráfico de aptidão

**What**: `aptidao` desenha a curva `teste` quando a coluna existe; sem a coluna, o gráfico sai como hoje, sem aviso.
**Where**: `graficos.py`
**Depends on**: T5
**Reuses**: `aptidao`, `GRAFICOS`
**Requirement**: PLOT-12, PLOT-15

**Done when**:

- [ ] `test_aptidao_com_curva_de_teste`: a figura tem uma curva de legenda `teste` com os valores da coluna, por geração
- [ ] `test_aptidao_sem_coluna_teste`: com o CSV de 12 colunas, aptidao.png é gravado sem curva `teste` e a saída não tem `Gráfico pulado` para ele
- [ ] Gate check passes: `python -m pytest test_ga.py test_modos.py test_registro.py test_pistas.py -v`
- [ ] Test count: os 126 testes anteriores + 2 de `test_pistas.py` passam (128)

**Tests**: unit
**Gate**: quick

**Commit**: `feat(plots): test curve in the fitness chart`

---

### T7: Comparação pela curva de teste

**What**: `comparacao` usa a coluna `teste` quando todos os treinos a têm e `media` caso contrário; o rótulo do eixo diz qual foi usada.
**Where**: `graficos.py`
**Depends on**: T6
**Reuses**: `comparacao`
**Requirement**: PLOT-13, PLOT-14

**Done when**:

- [ ] `test_comparacao_usa_teste`: com duas pastas no formato novo, cada curva de comparacao.png tem os valores de `teste` do treino
- [ ] `test_comparacao_sem_teste_usa_media`: com uma pasta nova e uma de 12 colunas, as duas curvas têm os valores de `media`
- [ ] Gate check passes: `python -m pytest test_ga.py test_modos.py test_registro.py test_pistas.py -v`
- [ ] Test count: os 128 testes anteriores + 2 de `test_pistas.py` passam (130)

**Tests**: unit
**Gate**: quick

**Commit**: `feat(plots): compare trainings by test score`

---

### T8: README e ferramenta de investigação

**What**: README descreve `--pistas`, o fitness médio, a coluna `teste`, o teto de frames e o `simula_pista.py`, que entra no repositório com esta tarefa.
**Where**: `README.md`
**Depends on**: T7
**Reuses**: seções atuais do README
**Requirement**: FIT-04, TST-03 (documentação)

**Done when**:

- [ ] README cita `--pistas`, as 13 colunas, as pistas de teste e `simula_pista.py`, e o comando de testes inclui `test_pistas.py`
- [ ] `simula_pista.py` versionado e compilando no Build
- [ ] Gate check passes: `python -m py_compile AGMLP.py DinoGame.py RedeNeural.py autodino.py graficos.py simula_pista.py; python -m pytest test_ga.py test_modos.py test_registro.py test_pistas.py -v`
- [ ] Test count: os 130 testes passam

**Tests**: none
**Gate**: build

**Commit**: `docs: fixed tracks, test score and the track simulator`

---

## Checks

**C1** - A população inteira corre em cada pista de treino, de sementes `semente + 1` a `semente + N` (FIT-01, Fitness AC 1)
Proof: run unit | test_pistas.py::test_populacao_corre_em_cada_pista_de_treino PASSED

**C2** - O fitness de cada indivíduo é a média dos scores dele nas pistas de treino (FIT-02, Fitness AC 2)
Proof: run unit | test_pistas.py::test_fitness_e_a_media_das_pistas PASSED

**C3** - As pistas de treino são as mesmas em todas as gerações (FIT-03, Fitness AC 3)
Proof: run unit | test_pistas.py::test_mesmas_pistas_em_todas_as_geracoes PASSED

**C4** - `--pistas N` troca as 5 pistas padrão por `N` (FIT-04, Fitness AC 4)
Proof: run unit | test_pistas.py::test_opcao_pistas PASSED

**C5** - `--pistas` menor que 1 ou não inteiro: código de saída 2, sem treinar (FIT-05, Fitness AC 5)
Proof: run unit | test_pistas.py::test_pistas_invalido_codigo_2 PASSED

**C6** - Um dino vivo no frame 14000 encerra a partida com o score desse frame (FIT-06, Fitness AC 6)
Proof: run unit | test_pistas.py::test_teto_de_frames PASSED

**C7** - `melhor`, `media`, `mediana`, `desvio` e `pior` são estatísticas dos fitness (FIT-07, Fitness AC 7)
Proof: run unit | test_pistas.py::test_estatisticas_sobre_o_fitness PASSED

**C8** - `frames`, `mortes_cacto` e `mortes_ptera` somam todas as pistas de treino (FIT-08, Fitness AC 8)
Proof: run unit | test_pistas.py::test_frames_e_mortes_somam_as_pistas PASSED

**C9** - `obstaculos_melhor` e `obstaculos_media` vêm da média por pista de cada dino (FIT-09, Fitness AC 9)
Proof: run unit | test_pistas.py::test_obstaculos_media_por_pista PASSED

**C10** - `bestDino.din` é regravado quando o maior fitness da geração supera o recorde (FIT-10, Fitness AC 10)
Proof: run unit | test_pistas.py::test_recorde_pelo_fitness PASSED

**C11** - `config.json` traz `pistas`, `pistas_teste` e `limite_frames` (FIT-11, Fitness AC 11)
Proof: run unit | test_pistas.py::test_config_traz_pistas PASSED

**C12** - A melhor rede da geração corre nas 20 pistas de teste, sementes 900001 a 900020 (TST-01, Teste AC 1)
Proof: run unit | test_pistas.py::test_melhor_corre_nas_pistas_de_teste PASSED

**C13** - `teste` é a média dos scores dessa rede nas pistas de teste (TST-02, Teste AC 2)
Proof: run unit | test_pistas.py::test_coluna_teste_e_a_media PASSED

**C14** - O cabeçalho do `fitness.csv` é o de 13 colunas, terminando em `teste` (TST-03, Teste AC 3)
Proof: run unit | test_pistas.py::test_cabecalho_com_teste PASSED

**C15** - A seleção e a reprodução não usam os scores de teste (TST-04, Teste AC 4)
Proof: run unit | test_pistas.py::test_selecao_ignora_o_teste PASSED

**C16** - As pistas de teste são as mesmas para qualquer `--semente` e `--pistas` (TST-05, Teste AC 5)
Proof: run unit | test_pistas.py::test_pistas_de_teste_independem_das_opcoes PASSED

**C17** - `resumo.json` traz `teste_do_melhor`, o `teste` da geração do recorde (TST-06, Teste AC 6)
Proof: run unit | test_pistas.py::test_resumo_traz_teste_do_melhor PASSED

**C18** - Sem janela, cada geração imprime `Geração <g>: melhor=<melhor> media=<media> teste=<teste>` (TST-07, Teste AC 7)
Proof: run unit | test_pistas.py::test_linha_impressa_com_teste PASSED

**C19** - Com e sem janela, as mesmas opções dão `fitness.csv` idênticos (TST-08, Teste AC 8)
Proof: run unit | test_pistas.py::test_csv_igual_com_e_sem_janela_com_pistas PASSED

**C20** - aptidao.png traz a curva `teste` quando a coluna existe (PLOT-12, Gráficos AC 1)
Proof: run unit | test_pistas.py::test_aptidao_com_curva_de_teste PASSED

**C21** - comparacao.png desenha a curva de teste quando todas as pastas a têm (PLOT-13, Gráficos AC 2)
Proof: run unit | test_pistas.py::test_comparacao_usa_teste PASSED

**C22** - comparacao.png desenha a média quando alguma pasta não tem `teste` (PLOT-14, Gráficos AC 3)
Proof: run unit | test_pistas.py::test_comparacao_sem_teste_usa_media PASSED

**C23** - Sem a coluna `teste`, aptidao.png sai sem a curva e sem aviso (PLOT-15, Gráficos AC 4)
Proof: run unit | test_pistas.py::test_aptidao_sem_coluna_teste PASSED

**C24** - `--pistas 1` usa só a pista de semente `semente + 1` em todas as gerações (FIT-12, Edge case 1)
Proof: run unit | test_pistas.py::test_uma_pista_so PASSED

**C25** - Janela fechada durante qualquer pista: a geração não é registrada (FIT-13, Edge case 2)
Proof: run unit | test_pistas.py::test_janela_fechada_nao_registra_geracao PASSED

**C26** - Empate no maior fitness: a escolha é a mesma em execuções repetidas (TST-09, Edge case 3)
Proof: run unit | test_pistas.py::test_empate_no_melhor_e_reproduzivel PASSED

---

## Handoff

**Settled mid-build:** 2026-11-23 - execução inline, sem sub-agentes de lote (8 tarefas, um lote); informado com o plano, usuário: "Aprovado, pode aplicar."
**Dispatched:** none
**Walked:** none

---

## Phase Execution Map

```
Phase 1 → Phase 2

Phase 1:  T1 → T2 → T3 → T4 → T5
Phase 2:  T5 → T6 → T7 → T8
```

8 tarefas: cabem em um lote, execução inline, sem sub-agentes de lote.

---

## Task Granularity Check

| Task | Scope | Status |
| ---- | ----- | ------ |
| T1: Teto de frames por partida | 1 método (`roda_geracao`) | ✅ Granular |
| T2: Avaliação em várias pistas | 1 método novo (`avalia`) | ✅ Granular |
| T3: Treino com pistas fixas | 1 método (`train`) + testes antigos atualizados | ⚠️ OK, coeso |
| T4: Pistas de teste | 1 método (`train`) + 1 coluna em `registra_geracao` | ⚠️ OK, coeso |
| T5: Opção --pistas | 1 opção em `main` | ✅ Granular |
| T6: Curva de teste no gráfico de aptidão | 1 função de gráfico | ✅ Granular |
| T7: Comparação pela curva de teste | 1 função de gráfico | ✅ Granular |
| T8: README e ferramenta de investigação | 1 arquivo + 1 script já escrito | ✅ Granular |

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

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| ---- | --------------------------- | --------------- | --------- | ------ |
| T1 | Laço de treino | integration | integration | ✅ OK |
| T2 | Laço de treino | integration | integration | ✅ OK |
| T3 | Laço de treino | integration | integration | ✅ OK |
| T4 | Laço de treino | integration | integration | ✅ OK |
| T5 | Linha de comando | integration | integration | ✅ OK |
| T6 | Gráficos | unit | unit | ✅ OK |
| T7 | Gráficos | unit | unit | ✅ OK |
| T8 | Documentação e ferramenta de investigação | none | none | ✅ OK |
