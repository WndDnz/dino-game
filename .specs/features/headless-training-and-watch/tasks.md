# Headless Training and Watch Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/headless-training-and-watch/design.md`
**Status**: In Progress
**Approved**: 2026-11-22 - user: "Aprovo, pode executar."
**Build**: `python -m py_compile AGMLP.py DinoGame.py RedeNeural.py autodino.py`
**Run unit**: `python -m pytest test_ga.py test_modos.py -v`

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: none - strong defaults applied. Padrão existente: `test_ga.py` na raiz, pytest, driver SDL `dummy`.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| Rede neural (`RedeNeural.py`) | unit | 1:1 com os critérios da spec | `test_modos.py` | `python -m pytest test_ga.py test_modos.py -v` |
| Sprites, máscaras, pista e sensor (`DinoGame.py`: `Pista`, `cacto_a_frente`, `carrega_rede`, propriedade `mask`) | unit | 1:1 com os critérios e casos de borda da spec | `test_modos.py` | `python -m pytest test_ga.py test_modos.py -v` |
| Laços de jogo e treino (`DinoGame.py`: `gameplay`, `roda_geracao`, `train`) | integration | Todo critério da spec que o laço realiza, rodando o laço de verdade com driver `dummy` | `test_modos.py` | `python -m pytest test_ga.py test_modos.py -v` |
| Linha de comando (`autodino.py`) | integration | Todas as opções: caminho normal, opções inválidas e arquivos com erro; os critérios de processo rodam em processo novo | `test_modos.py` | `python -m pytest test_ga.py test_modos.py -v` |

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | Depois de tarefas com testes unitários | `python -m pytest test_ga.py test_modos.py -v` |
| Full | Depois de tarefas com testes de integração | `python -m pytest test_ga.py test_modos.py -v` |
| Build | Fim de fase | `python -m py_compile AGMLP.py DinoGame.py RedeNeural.py autodino.py; python -m pytest test_ga.py test_modos.py -v` |

---

## Execution Plan

Execução estritamente sequencial, T1 a T10.

### Phase 1: Base de desempenho

```
T1 → T2
```

### Phase 2: Pista

```
T2 → T3 → T4 → T5
```

### Phase 3: Treino

```
T5 → T6 → T7
```

### Phase 4: Assistir e linha de comando

```
T7 → T8 → T9 → T10
```

---

## Task Breakdown

### T1: Sprites em cache e máscara pronta

**What**: As folhas de sprites são carregadas uma vez, e `Dino`, `Cactus` e `Ptera` ganham a propriedade `mask` com a máscara da imagem atual.
**Where**: `DinoGame.py`
**Depends on**: None
**Reuses**: `DinoGame.load_sprite_sheet`
**Requirement**: HEAD-05 (suporte)

**Done when**:

- [x] `test_mascara_em_cache_igual_a_da_imagem`: para dino em pé, abaixado, cacto e ptera, `sprite.mask` tem os mesmos bits de `pygame.mask.from_surface(sprite.image)`
- [x] `test_sprites_carregados_uma_vez`: criar 50 dinos chama `pygame.image.load` no máximo 2 vezes
- [x] Gate check passes: `python -m pytest test_ga.py test_modos.py -v`
- [x] Test count: 25 testes de `test_ga.py` + 2 de `test_modos.py` passam

**Tests**: unit
**Gate**: quick

**Commit**: `perf(game): cache sprite sheets and collision masks`

---

### T2: Decisão em lote

**What**: `RedeNeural.empilha(redes)` e `RedeNeural.feed_forward_lote(W, B, a)` calculam a saída de N redes em uma operação.
**Where**: `RedeNeural.py`
**Depends on**: T1
**Reuses**: sigmoide de `feedForward`
**Requirement**: HEAD-05 (suporte)

**Done when**:

- [x] `test_lote_igual_ao_individual`: para 50 redes e entradas diferentes por rede, o lote é igual a `feedForward` de cada uma (`np.allclose`), inclusive para um subconjunto de índices
- [x] Gate check passes: `python -m pytest test_ga.py test_modos.py -v`
- [x] Test count: 25 testes de `test_ga.py` + 3 de `test_modos.py` passam

**Tests**: unit
**Gate**: quick

**Commit**: `perf(rede): batched feed-forward`

---

### T3: Classe Pista

**What**: `Pista` cria e move obstáculos, nuvens e chão pelas regras do jogo manual, com distância mínima de 160 px entre um obstáculo novo e os que já estão na tela.
**Where**: `DinoGame.py`
**Depends on**: T2
**Reuses**: regras de `gameplay` (`DinoGame.py:274-304`), `Cactus`, `Ptera`, `Cloud`, `Ground`
**Requirement**: TRACK-02, TRACK-01 (regras)

**Done when**:

- [x] `test_obstaculo_novo_a_160_px`: em 20 sementes x 5000 frames, todo obstáculo criado tem a borda esquerda a 160 px ou mais da borda direita de cada obstáculo presente
- [x] `test_pista_regras_do_jogo_manual`: nas mesmas pistas, nunca mais de 2 cactos na tela, nenhum ptera antes do frame 700, todo ptera com 46x40, velocidade 4 no início e +1 a cada 700 frames
- [x] Gate check passes: `python -m pytest test_ga.py test_modos.py -v`
- [x] Test count: 25 testes de `test_ga.py` + 5 de `test_modos.py` passam

**Tests**: unit
**Gate**: quick

**Commit**: `feat(game): track class with minimum obstacle distance`

---

### T4: Cacto à frente

**What**: Função `cacto_a_frente(dino, cacti)` devolve o cacto mais próximo cuja borda direita ainda não passou da borda esquerda do dino, ou `None`.
**Where**: `DinoGame.py`
**Depends on**: T3
**Reuses**: `sensores`
**Requirement**: TRACK-03, TRACK-04

**Done when**:

- [x] `test_sensor_mede_cacto_mais_proximo_a_frente`: com um cacto já passado, um a 200 px e um a 400 px, `sensores(dino, cacto_a_frente(...), None, 4)` dá `l` = 200 / 600; o resultado não depende da ordem dos cactos no grupo
- [x] `test_sensor_vale_1_quando_cactos_passaram`: com todos os cactos passados, `l` = 1.0; um cacto com a borda direita exatamente na borda esquerda do dino ainda conta como à frente
- [x] Gate check passes: `python -m pytest test_ga.py test_modos.py -v`
- [x] Test count: 25 testes de `test_ga.py` + 7 de `test_modos.py` passam

**Tests**: unit
**Gate**: quick

**Commit**: `feat(game): pick the nearest cactus ahead for the sensor`

---

### T5: Jogo manual na Pista

**What**: `gameplay` usa `Pista` no lugar das regras próprias de criação de obstáculos.
**Where**: `DinoGame.py`
**Depends on**: T4
**Reuses**: `Pista` (T3)
**Requirement**: TRACK-01 (jogo manual)

**Done when**:

- [x] `test_jogo_manual_usa_a_pista`: com a mesma semente e colisões desligadas, a sequência (frame, tipo, posição) dos obstáculos criados em 1500 frames de `gameplay` é igual à de uma `Pista` rodada sozinha
- [x] Gate check passes: `python -m pytest test_ga.py test_modos.py -v`
- [x] Test count: 25 testes de `test_ga.py` + 8 de `test_modos.py` passam

**Tests**: integration
**Gate**: full

**Commit**: `refactor(game): manual game runs on the shared track`

---

### T6: Uma geração, com ou sem janela

**What**: Método `roda_geracao(redes, janela)` simula uma geração na `Pista` com decisão em lote e devolve os pares `(score, rede)`; com `janela`, trata eventos, desenha dinos e HUD e limita o FPS.
**Where**: `DinoGame.py`
**Depends on**: T5
**Reuses**: `Pista`, `cacto_a_frente`, `sensores`, `Dino.agir`, `remove_colididos`, `feed_forward_lote`
**Requirement**: HEAD-05, WIN-02

**Done when**:

- [x] `test_roda_geracao_devolve_um_par_por_dino`: 10 redes, sem janela, devolve 10 pares, cada rede uma vez
- [x] `test_treino_com_janela_desenha_dinos_e_hud`: com janela (driver dummy), a tela tem pixels do dino na posição dele e pixels vermelhos e azuis do HUD; sem janela, a tela não é tocada
- [x] `test_sem_janela_metade_do_tempo`: com 350 dinos mantidos vivos por 150 frames, o tempo sem janela é no máximo 1/2 do tempo com janela (mediana de 3 medições)
- [x] Gate check passes: `python -m pytest test_ga.py test_modos.py -v`
- [x] Test count: 25 testes de `test_ga.py` + 11 de `test_modos.py` passam

**Tests**: integration
**Gate**: full

**Commit**: `feat(game): run one generation with or without a window`

---

### T7: Treino em laço de gerações

**What**: `train(..., janela=True)` vira um laço que chama `roda_geracao`, sem recursão; sem janela imprime `Geração <g>: melhor=<score> media=<media>` e retorna ao fim da última geração.
**Where**: `DinoGame.py`
**Depends on**: T6
**Reuses**: `roda_geracao` (T6), `registra_geracao`, `RNA_AG`
**Requirement**: HEAD-02, HEAD-03, HEAD-06, HEAD-08, TRACK-01 (treino)

**Done when**:

- [ ] `test_mesmo_csv_com_e_sem_janela`: N=10, 3 gerações, mesma semente: `fitness.csv` idênticos
- [ ] `test_imprime_linha_por_geracao`: 2 gerações sem janela imprimem 2 linhas no formato, com os valores do `fitness.csv`
- [ ] `test_pilha_nao_cresce_entre_geracoes`: a profundidade da pilha na criação do primeiro obstáculo é igual nas gerações 1, 2 e 3
- [ ] `test_sem_janela_interrompido_mantem_melhor`: `KeyboardInterrupt` na geração 2 de 3 deixa `bestDino.din` com a melhor rede da geração 1
- [ ] Os 25 testes de `test_ga.py` continuam passando sem alteração
- [ ] Gate check passes: `python -m pytest test_ga.py test_modos.py -v`
- [ ] Test count: 25 testes de `test_ga.py` + 15 de `test_modos.py` passam

**Tests**: integration
**Gate**: full

**Commit**: `feat(game): generation loop and headless training`

---

### T8: Carregar a rede salva

**What**: Função `carrega_rede(caminho)` devolve a `RedeNeural` do arquivo; levanta `FileNotFoundError` se ele não existe e `ValueError` se não for uma rede `(5, 8, 4, 2)`.
**Where**: `DinoGame.py`
**Depends on**: T7
**Reuses**: `RedeNeural.load_object`
**Requirement**: WATCH-09, WATCH-10 (suporte)

**Done when**:

- [ ] `test_carrega_rede_devolve_a_rede_salva`: pesos e bias iguais aos da rede gravada
- [ ] `test_carrega_rede_arquivo_inexistente_levanta`: `FileNotFoundError`
- [ ] `test_carrega_rede_arquivo_invalido_levanta`: `ValueError` para rede `(5, 4, 2)`, para um objeto que não é `RedeNeural` e para um arquivo que não é pickle
- [ ] Gate check passes: `python -m pytest test_ga.py test_modos.py -v`
- [ ] Test count: 25 testes de `test_ga.py` + 18 de `test_modos.py` passam

**Tests**: unit
**Gate**: quick

**Commit**: `feat(game): load and validate a saved network`

---

### T9: Assistir: a rede joga o jogo manual

**What**: `gameplay(rede=None, semente=None)`: com `rede`, a ação do dino vem da rede a cada frame; com `semente`, cada partida começa com `random.seed(semente)`.
**Where**: `DinoGame.py`
**Depends on**: T8
**Reuses**: placar, fim de jogo e reinício de `gameplay`; `sensores`, `cacto_a_frente`, `Dino.agir`
**Requirement**: WATCH-01, WATCH-03, WATCH-04, WATCH-05, WATCH-06, WATCH-07, WATCH-08, TRACK-01

**Done when**:

- [ ] `test_assistir_rede_controla_o_dino_a_60_fps`: uma rede que sempre pula faz o dino sair do chão sem tecla; uma que nunca pula deixa o dino no chão; o laço limita a 60 FPS
- [ ] `test_assistir_mostra_pontuacao`: a região do placar na tela muda quando a pontuação sobe
- [ ] `test_assistir_usa_regras_do_jogo_manual`: a sequência de obstáculos é a da `Pista` com a mesma semente
- [ ] `test_assistir_colisao_mostra_fim_de_jogo`: depois da colisão a pontuação para de subir e a tela de fim de jogo é desenhada
- [ ] `test_assistir_espaco_reinicia_com_a_mesma_rede`: ESPAÇO e ENTER na tela de fim iniciam outra partida controlada pela mesma rede
- [ ] `test_assistir_esc_encerra_com_codigo_0`: ESC e fechar a janela encerram com `SystemExit` de código 0
- [ ] `test_assistir_semente_por_partida`: com `semente=5`, o primeiro obstáculo de duas partidas seguidas nasce com o `random` recém-semeado em 5; sem semente, não
- [ ] `test_tres_modos_mesma_pista`: jogo manual, treino e assistir, com a mesma semente e colisões desligadas, criam a mesma sequência de obstáculos em 1500 frames
- [ ] Gate check passes: `python -m pytest test_ga.py test_modos.py -v`
- [ ] Test count: 25 testes de `test_ga.py` + 26 de `test_modos.py` passam

**Tests**: integration
**Gate**: full

**Commit**: `feat(game): watch a saved network play the manual game`

---

### T10: Linha de comando

**What**: `autodino.main(argv)` com `--sem-janela`, `--assistir [arquivo]`, `--individuos`, `--geracoes`, `--semente`; devolve o código de saída.
**Where**: `autodino.py`
**Depends on**: T9
**Reuses**: `DinoGame.start`, `train`, `gameplay`, `carrega_rede`
**Requirement**: HEAD-01, HEAD-04, HEAD-07, WATCH-02, WATCH-09, WATCH-10, WIN-01, CLI-01, CLI-02

**Done when**:

- [ ] `test_sem_janela_usa_driver_dummy`: em um processo novo sem `SDL_VIDEODRIVER`, `--sem-janela` deixa `pygame.display.get_driver()` igual a `dummy`
- [ ] `test_sem_janela_termina_com_codigo_0`: `python autodino.py --sem-janela --individuos 10 --geracoes 2` termina sozinho com código 0, 2 linhas de geração e `fitness.csv` com 2 linhas de dados
- [ ] `test_opcoes_de_treino_sao_usadas`: `--individuos 7 --geracoes 2 --semente 9` treina 7 dinos por 2 gerações com semente 9; sem as opções, 350, 30 e 0
- [ ] `test_assistir_carrega_o_arquivo_indicado`: `--assistir outro.din` joga com a rede de `outro.din`; sem caminho, com a de `bestDino.din`
- [ ] `test_assistir_arquivo_inexistente`: imprime `Arquivo não encontrado: <caminho>`, código 1, nenhuma janela criada
- [ ] `test_assistir_arquivo_invalido`: imprime `Arquivo inválido: <caminho>`, código 1, nenhuma janela criada
- [ ] `test_sem_opcoes_treina_350_por_30_com_janela`: sem opções, passa pela tela inicial e treina 350 por 30 com janela
- [ ] `test_individuos_ou_geracoes_menor_que_1`: 0 e -1 em cada opção dão código 2, sem treinar
- [ ] `test_sem_janela_com_assistir_e_erro`: as duas opções juntas dão código 2
- [ ] Gate check passes: `python -m pytest test_ga.py test_modos.py -v`
- [ ] Test count: 25 testes de `test_ga.py` + 35 de `test_modos.py` passam

**Tests**: integration
**Gate**: full

**Commit**: `feat(cli): headless training and watch options`

---

## Checks

**C1** - `--sem-janela` roda com o driver de vídeo `dummy` (HEAD-01, AC 1)
Proof: run unit | test_modos.py::test_sem_janela_usa_driver_dummy PASSED

**C2** - Mesmos N, gerações e semente: `fitness.csv` idêntico com e sem janela (HEAD-02, AC 2)
Proof: run unit | test_modos.py::test_mesmo_csv_com_e_sem_janela PASSED

**C3** - Cada geração sem janela imprime `Geração <g>: melhor=<score> media=<media>` (HEAD-03, AC 3)
Proof: run unit | test_modos.py::test_imprime_linha_por_geracao PASSED

**C4** - Depois da última geração o processo sem janela sai com código 0, sem esperar tecla (HEAD-04, AC 4)
Proof: run unit | test_modos.py::test_sem_janela_termina_com_codigo_0 PASSED

**C5** - Com 350 dinos vivos, um frame sem janela custa no máximo 1/2 de um frame com janela (HEAD-05, AC 5)
Proof: run unit | test_modos.py::test_sem_janela_metade_do_tempo PASSED

**C6** - A profundidade da pilha é a mesma em todas as gerações (HEAD-06, AC 6)
Proof: run unit | test_modos.py::test_pilha_nao_cresce_entre_geracoes PASSED

**C7** - `--individuos`, `--geracoes` e `--semente` substituem 350, 30 e 0 (HEAD-07, AC 7)
Proof: run unit | test_modos.py::test_opcoes_de_treino_sao_usadas PASSED

**C8** - Treino sem janela interrompido deixa em `bestDino.din` a melhor rede das gerações concluídas (HEAD-08, Edge Case 3)
Proof: run unit | test_modos.py::test_sem_janela_interrompido_mantem_melhor PASSED

**C9** - No modo assistir um único dino é controlado pela rede, a 60 frames por segundo (WATCH-01, AC 1)
Proof: run unit | test_modos.py::test_assistir_rede_controla_o_dino_a_60_fps PASSED

**C10** - `--assistir <caminho>` carrega a rede desse arquivo; sem caminho, `bestDino.din` (WATCH-02, AC 2)
Proof: run unit | test_modos.py::test_assistir_carrega_o_arquivo_indicado PASSED

**C11** - A pontuação do dino aparece na tela durante a partida (WATCH-03, AC 3)
Proof: run unit | test_modos.py::test_assistir_mostra_pontuacao PASSED

**C12** - O modo assistir gera obstáculos pelas regras do jogo manual (WATCH-04, AC 4)
Proof: run unit | test_modos.py::test_assistir_usa_regras_do_jogo_manual PASSED

**C13** - A colisão para a partida e mostra a tela de fim de jogo (WATCH-05, AC 5)
Proof: run unit | test_modos.py::test_assistir_colisao_mostra_fim_de_jogo PASSED

**C14** - ESPAÇO ou ENTER na tela de fim inicia outra partida com a mesma rede (WATCH-06, AC 6)
Proof: run unit | test_modos.py::test_assistir_espaco_reinicia_com_a_mesma_rede PASSED

**C15** - ESC ou fechar a janela encerra com código 0 (WATCH-07, AC 7)
Proof: run unit | test_modos.py::test_assistir_esc_encerra_com_codigo_0 PASSED

**C16** - Com `--semente S`, cada partida começa com `random.seed(S)` (WATCH-08, AC 8)
Proof: run unit | test_modos.py::test_assistir_semente_por_partida PASSED

**C17** - Arquivo inexistente: `Arquivo não encontrado: <caminho>`, código 1, sem janela (WATCH-09, AC 9)
Proof: run unit | test_modos.py::test_assistir_arquivo_inexistente PASSED

**C18** - Arquivo que não é uma rede `(5, 8, 4, 2)`: `Arquivo inválido: <caminho>`, código 1, sem janela (WATCH-10, AC 10)
Proof: run unit | test_modos.py::test_assistir_arquivo_invalido PASSED

**C19** - Sem opções: tela inicial e depois treino de 350 dinos por 30 gerações com janela (WIN-01, AC 1)
Proof: run unit | test_modos.py::test_sem_opcoes_treina_350_por_30_com_janela PASSED

**C20** - O treino com janela desenha os dinos vivos e o HUD (WIN-02, AC 2)
Proof: run unit | test_modos.py::test_treino_com_janela_desenha_dinos_e_hud PASSED

**C21** - Jogo manual, treino e assistir criam a mesma sequência de obstáculos para a mesma semente (TRACK-01, AC 1)
Proof: run unit | test_modos.py::test_tres_modos_mesma_pista PASSED

**C22** - Todo obstáculo novo nasce a 160 px ou mais dos que estão na tela (TRACK-02, AC 2)
Proof: run unit | test_modos.py::test_obstaculo_novo_a_160_px PASSED

**C23** - Com mais de um cacto, o sensor mede o mais próximo que ainda não passou pelo dino (TRACK-03, AC 3)
Proof: run unit | test_modos.py::test_sensor_mede_cacto_mais_proximo_a_frente PASSED

**C24** - Com todos os cactos já passados, o sensor de cacto vale 1.0 (TRACK-04, AC 4)
Proof: run unit | test_modos.py::test_sensor_vale_1_quando_cactos_passaram PASSED

**C25** - `--individuos` ou `--geracoes` menor que 1: erro de uso, código 2, sem treinar (CLI-01, Edge Case 1)
Proof: run unit | test_modos.py::test_individuos_ou_geracoes_menor_que_1 PASSED

**C26** - `--sem-janela` com `--assistir`: erro de uso, código 2 (CLI-02, Edge Case 2)
Proof: run unit | test_modos.py::test_sem_janela_com_assistir_e_erro PASSED

---

## Handoff

**Settled mid-build:** 2026-11-22 - execução inline, sem sub-agentes: oferta feita com o plano ("Aprova o plano de tarefas, com execução nesta sessão?"), usuário: "Aprovo, pode executar."
**Dispatched:** none
**Walked:** none

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4

Phase 1:  T1 → T2
Phase 2:  T2 → T3 → T4 → T5
Phase 3:  T5 → T6 → T7
Phase 4:  T7 → T8 → T9 → T10
```

10 tarefas: passa do limite de ~8 de um lote. A oferta de sub-agentes vem antes da primeira tarefa.

---

## Task Granularity Check

| Task | Scope | Status |
| ---- | ----- | ------ |
| T1: Sprites em cache e máscara pronta | 1 cache + 1 propriedade em 3 classes | ⚠️ OK, coeso |
| T2: Decisão em lote | 2 funções estáticas | ⚠️ OK, coeso |
| T3: Classe Pista | 1 classe | ✅ Granular |
| T4: Cacto à frente | 1 função | ✅ Granular |
| T5: Jogo manual na Pista | 1 função (`gameplay`) | ✅ Granular |
| T6: Uma geração, com ou sem janela | 1 método | ✅ Granular |
| T7: Treino em laço de gerações | 1 função (`train`) | ✅ Granular |
| T8: Carregar a rede salva | 1 função | ✅ Granular |
| T9: Assistir: a rede joga o jogo manual | 1 função (`gameplay`) | ✅ Granular |
| T10: Linha de comando | 1 função (`main`) | ✅ Granular |

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

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| ---- | --------------------------- | --------------- | --------- | ------ |
| T1 | Sprites, máscaras, pista e sensor | unit | unit | ✅ OK |
| T2 | Rede neural | unit | unit | ✅ OK |
| T3 | Sprites, máscaras, pista e sensor | unit | unit | ✅ OK |
| T4 | Sprites, máscaras, pista e sensor | unit | unit | ✅ OK |
| T5 | Laços de jogo e treino | integration | integration | ✅ OK |
| T6 | Laços de jogo e treino | integration | integration | ✅ OK |
| T7 | Laços de jogo e treino | integration | integration | ✅ OK |
| T8 | Sprites, máscaras, pista e sensor | unit | unit | ✅ OK |
| T9 | Laços de jogo e treino | integration | integration | ✅ OK |
| T10 | Linha de comando | integration | integration | ✅ OK |
