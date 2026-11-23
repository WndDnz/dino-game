# Training Record and Plots Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: none - fase Design pulada; as decisões de estrutura estão em "Design inline" abaixo
**Status**: In Progress
**Approved**: 2026-11-23 - user: "Aprovo, pode executar."
**Build**: `python -m py_compile AGMLP.py DinoGame.py RedeNeural.py autodino.py`
**Run unit**: `python -m pytest test_ga.py test_modos.py test_registro.py -v`

---

## Design inline

- **Quem conta o quê**: `roda_geracao` é o único lugar que vê os frames, as colisões e os obstáculos passando. Ela preenche `Dino.obstaculos` e `Dino.causa` e deixa em `self.estatisticas` um dicionário com `frames`, `obstaculos` (um valor por dino), `mortes_cacto` e `mortes_ptera`. A lista `[(score, rede)]` que ela devolve não muda.
- **Quem grava o quê**: `registra_geracao(ranked, geracao, melhor_score, saida, estatisticas=None)` calcula mediana, desvio, pior e diversidade a partir de `ranked` e grava a linha de 12 colunas; sem `estatisticas`, as colunas de frames, obstáculos e mortes valem 0. `train` grava `config.json` e `resumo.json` em `saida`. `autodino.main` só decide qual é a pasta.
- **Hiperparâmetros**: os valores que hoje estão soltos no código viram constantes de módulo (`AGMLP.SIGMA_MUTACAO`, `TORNEIO`, `ALPHA_BLX`; `DinoGame.TOPOLOGIA`, `TAXA_MUTACAO`, `ELITE`), usadas pelo treino e lidas pelo `config.json`, para o registro não poder divergir do que rodou.
- **Reprodutibilidade**: nada que dependa do relógio entra no `fitness.csv`; `inicio` vai para `config.json` e `segundos_total` para `resumo.json`.
- **Gráficos**: `graficos.py` na raiz, com uma função por gráfico que recebe as linhas do CSV e devolve a figura do matplotlib; `main(argv)` lê, grava os PNG e devolve o código de saída. Sem `--mostrar`, usa o backend `Agg`.
- **Testes**: arquivo novo `test_registro.py` na raiz, no padrão dos outros dois (driver SDL `dummy`), com `MPLBACKEND=Agg`.

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: none - strong defaults applied. Padrão existente: `test_ga.py` e `test_modos.py` na raiz, pytest, driver SDL `dummy`.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| Algoritmo genético (`AGMLP.py`) | unit | 1:1 com os critérios da spec | `test_registro.py` | `python -m pytest test_ga.py test_modos.py test_registro.py -v` |
| Métricas e registro (`DinoGame.py`: `registra_geracao`, `versao_do_codigo`) | unit | 1:1 com os critérios e casos de borda da spec | `test_registro.py` | `python -m pytest test_ga.py test_modos.py test_registro.py -v` |
| Laço de treino (`DinoGame.py`: `roda_geracao`, `train`) | integration | Todo critério que o laço realiza, rodando o laço de verdade com driver `dummy` | `test_registro.py` | `python -m pytest test_ga.py test_modos.py test_registro.py -v` |
| Linha de comando (`autodino.py`) | integration | Todas as opções: caminho normal, pasta recusada, sem treino | `test_registro.py` | `python -m pytest test_ga.py test_modos.py test_registro.py -v` |
| Gráficos (`graficos.py`) | unit | 1:1 com os critérios e casos de borda da spec, conferindo os dados de cada figura | `test_registro.py` | `python -m pytest test_ga.py test_modos.py test_registro.py -v` |
| Documentação e configuração (`README.md`, `.gitignore`) | none | - (build gate only) | - | build gate only |

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | Depois de tarefas com testes unitários | `python -m pytest test_ga.py test_modos.py test_registro.py -v` |
| Full | Depois de tarefas com testes de integração | `python -m pytest test_ga.py test_modos.py test_registro.py -v` |
| Build | Fim de fase ou tarefa sem teste | `python -m py_compile AGMLP.py DinoGame.py RedeNeural.py autodino.py; python -m pytest test_ga.py test_modos.py test_registro.py -v` (a partir de T9, com `graficos.py` no `py_compile`) |

---

## Execution Plan

Execução estritamente sequencial, T1 a T12.

### Phase 1: Métricas

```
T1 → T2 → T3 → T4
```

### Phase 2: Registro

```
T4 → T5 → T6 → T7 → T8
```

### Phase 3: Gráficos

```
T8 → T9 → T10 → T11
```

### Phase 4: Documentação

```
T11 → T12
```

---

## Task Breakdown

### T1: Diversidade da população

**What**: Função `diversidade(redes)`: média, sobre os genes, do desvio padrão de cada gene entre as redes.
**Where**: `AGMLP.py`
**Depends on**: None
**Reuses**: numpy
**Requirement**: MET-06 (suporte)

**Done when**:

- [x] `test_diversidade_media_do_desvio_por_gene`: 0.0 para redes idênticas; para duas redes que diferem de 2.0 em todos os genes, 1.0; para 3 redes construídas à mão, o valor calculado gene a gene
- [x] Gate check passes: `python -m pytest test_ga.py test_modos.py test_registro.py -v`
- [x] Test count: os 70 testes existentes + 1 de `test_registro.py` passam

**Tests**: unit
**Gate**: quick

**Commit**: `feat(ag): population diversity measure`

---

### T2: Hiperparâmetros em constantes

**What**: `SIGMA_MUTACAO`, `TORNEIO` e `ALPHA_BLX` viram constantes de módulo, usadas como padrão por `aplicaMutacao`, `selecao` e `acasala`.
**Where**: `AGMLP.py`
**Depends on**: T1
**Reuses**: os valores atuais: 0.5, 3 e 0.1
**Requirement**: REC-02 (suporte)

**Done when**:

- [x] `test_hiperparametros_do_ag_sao_as_constantes`: as constantes valem 0.5, 3 e 0.1; trocar `TORNEIO` para 1 faz o torneio devolver indivíduos sorteados sem preferência pelo melhor; com `SIGMA_MUTACAO` 2.0 o desvio dos deltas da mutação fica entre 1.8 e 2.2; com `ALPHA_BLX` 0.0 todo gene do filho fica entre os dos pais
- [x] Gate check passes: `python -m pytest test_ga.py test_modos.py test_registro.py -v`
- [x] Test count: os 70 testes existentes + 2 de `test_registro.py` passam

**Tests**: unit
**Gate**: quick

**Commit**: `refactor(ag): name the genetic hyperparameters`

---

### T3: Contadores por dino e por geração

**What**: `roda_geracao` conta os frames, os obstáculos vencidos por cada dino e as mortes por cacto e por ptera, e guarda tudo em `self.estatisticas`.
**Where**: `DinoGame.py`
**Depends on**: T2
**Reuses**: `roda_geracao`, `remove_colididos`, `Pista`
**Requirement**: MET-03, MET-04, MET-05

**Done when**:

- [x] `test_frames_da_geracao`: `estatisticas['frames']` é o número de passos da pista naquela geração
- [x] `test_obstaculos_vencidos_por_dino`: com colisão só contra ptera e redes iguais, cada dino tem em `obstaculos` o número de cactos cuja borda direita passou da borda esquerda dele antes da morte, contado de forma independente pelo teste; um dino que morre no primeiro cacto tem 0
- [x] `test_mortes_por_tipo_de_obstaculo`: redes que nunca pulam morrem todas em cacto (`mortes_cacto` = N, `mortes_ptera` = 0); com colisão só contra ptera, o inverso; em uma geração de redes aleatórias as duas somam N
- [x] Gate check passes: `python -m pytest test_ga.py test_modos.py test_registro.py -v`
- [x] Test count: os 70 testes existentes + 5 de `test_registro.py` passam

**Tests**: integration
**Gate**: full

**Commit**: `feat(game): per-generation frames, obstacles cleared and deaths by type`

---

### T4: Registro por geração com todas as colunas

**What**: `registra_geracao` grava no `fitness.csv` as 12 colunas da spec; as asserções de cabeçalho e de linhas dos dois testes antigos passam ao formato novo.
**Where**: `DinoGame.py`
**Depends on**: T3
**Reuses**: `registra_geracao`, `AGMLP.diversidade`
**Requirement**: MET-01, MET-02, MET-06

**Done when**:

- [x] `test_cabecalho_do_fitness_csv`: a primeira linha é exatamente a da spec
- [x] `test_mediana_desvio_e_pior`: para scores 10, 20, 60 a linha traz mediana 20.0, desvio populacional 21.602468994692867 e pior 10; para um número par de scores a mediana é a média dos dois do meio
- [x] `test_diversidade_no_csv`: a coluna `diversidade` é `AGMLP.diversidade` das redes da geração
- [x] `test_ga.py` `test_csv_linha_por_geracao` e `test_modos.py` `test_sem_janela_termina_com_codigo_0` atualizados: mesmas verificações, no formato de 12 colunas (mudança aprovada pelo usuário na spec)
- [x] Gate check passes: `python -m pytest test_ga.py test_modos.py test_registro.py -v`
- [x] Test count: os 70 testes existentes + 8 de `test_registro.py` passam

**Tests**: unit
**Gate**: quick

**Commit**: `feat(game): extended per-generation record`

---

### T5: Versão do código

**What**: Função `versao_do_codigo()` devolve `(commit, alteracoes_locais)`: hash curto do git e se há alterações; `(None, False)` se o git não responder.
**Where**: `DinoGame.py`
**Depends on**: T4
**Reuses**: `subprocess`
**Requirement**: REC-10, REC-02 (suporte)

**Done when**:

- [x] `test_versao_do_codigo_vem_do_git`: o commit é igual à saída de `git rev-parse --short HEAD` do repositório, e `alteracoes_locais` é booleano
- [x] `test_versao_sem_git`: com o comando git indisponível, devolve `(None, False)` sem levantar erro
- [x] Gate check passes: `python -m pytest test_ga.py test_modos.py test_registro.py -v`
- [x] Test count: os 70 testes existentes + 10 de `test_registro.py` passam

**Tests**: unit
**Gate**: quick

**Commit**: `feat(game): read the code version from git`

---

### T6: Treino grava config, registro completo e resumo

**What**: `train` grava `config.json` antes da primeira geração, passa as estatísticas da geração a `registra_geracao` e grava `resumo.json` depois da última; topologia, taxa de mutação e elite viram constantes de módulo.
**Where**: `DinoGame.py`
**Depends on**: T5
**Reuses**: `roda_geracao` (T3), `registra_geracao` (T4), `versao_do_codigo` (T5), constantes de `AGMLP` (T2)
**Requirement**: REC-02, REC-03, REC-09, MET-07

**Done when**:

- [x] `test_config_json_antes_da_primeira_geracao`: `config.json` existe quando a primeira geração começa e tem as 13 chaves com os valores do treino (`individuos` 10, `geracoes` 2, `semente` 4, `janela` false, `topologia` [5, 8, 4, 2], `taxa_mutacao` 0.05, `sigma_mutacao` 0.5, `elite` 0.1, `torneio` 3, `alpha_blx` 0.1, `commit`, `alteracoes_locais`, `inicio` em formato ISO)
- [x] `test_resumo_json_no_fim`: `geracoes_concluidas` 3, `melhor_score` e `geracao_do_melhor` batem com o `fitness.csv`, `frames_total` é a soma da coluna `frames`, `segundos_total` é um número maior que 0
- [x] `test_treino_interrompido_sem_resumo`: interrompido na geração 2 de 3, a pasta tem `config.json`, `fitness.csv` com 1 linha de dados e `bestDino.din`, e não tem `resumo.json`
- [x] `test_csv_completo_igual_com_e_sem_janela`: N=10, 3 gerações, mesma semente: os dois `fitness.csv` de 12 colunas são idênticos, com `mortes_cacto + mortes_ptera` = 10 e `pior <= mediana <= melhor` em toda linha
- [x] Gate check passes: `python -m pytest test_ga.py test_modos.py test_registro.py -v`
- [x] Test count: os 70 testes existentes + 14 de `test_registro.py` passam

**Tests**: integration
**Gate**: full

**Commit**: `feat(game): training writes config, full record and summary`

---

### T7: Pasta por treino

**What**: `autodino.main` grava cada treino em `treinos/<AAAAMMDD-HHMMSS>_s<semente>` ou na pasta de `--saida`, recusa uma pasta que já tem `fitness.csv`, e `treinos/` entra no `.gitignore`.
**Where**: `autodino.py`
**Depends on**: T6
**Reuses**: `train(saida=...)`
**Requirement**: REC-01, REC-04, REC-05, REC-08

**Done when**:

- [ ] `test_treino_cria_pasta_com_data_e_semente`: `--sem-janela --semente 7` cria `treinos/<data-hora>_s7` com `fitness.csv` e `bestDino.din`, e não cria nenhum dos dois na pasta atual
- [ ] `test_saida_escolhida`: com `--saida meu_treino`, os arquivos vão para `meu_treino` e `treinos/` não é criada
- [ ] `test_pasta_com_treino_e_recusada`: `--saida` apontando para uma pasta com `fitness.csv` imprime `Pasta já tem um treino: <caminho>`, devolve 1 e deixa o arquivo intacto; uma pasta vazia existente é aceita
- [ ] `test_mesmo_segundo_ganha_sufixo`: dois treinos com a mesma semente no mesmo segundo criam `<nome>` e `<nome>-2`
- [ ] Gate check passes: `python -m pytest test_ga.py test_modos.py test_registro.py -v`
- [ ] Test count: os 70 testes existentes + 18 de `test_registro.py` passam

**Tests**: integration
**Gate**: full

**Commit**: `feat(cli): one folder per training run`

---

### T8: Assistir o treino mais recente

**What**: `--assistir` sem arquivo carrega o `bestDino.din` da pasta mais recente de `treinos/`; sem nenhuma, imprime `Nenhum treino encontrado em: treinos` e devolve 1.
**Where**: `autodino.py`
**Depends on**: T7
**Reuses**: `carrega_rede`
**Requirement**: REC-06, REC-07

**Done when**:

- [ ] `test_assistir_sem_arquivo_usa_o_treino_mais_recente`: com três pastas em `treinos/`, joga com a rede da de nome mais recente; uma pasta mais nova sem `bestDino.din` é ignorada; um `bestDino.din` na pasta atual não é usado
- [ ] `test_assistir_sem_nenhum_treino`: sem `treinos/` ou com ela vazia, imprime a mensagem, devolve 1 e não abre janela
- [ ] `test_modos.py` `test_assistir_carrega_o_arquivo_indicado` e `test_assistir_arquivo_inexistente`: os casos "sem caminho" passam a esperar o comportamento novo (mudança de WATCH-02 aprovada pelo usuário na spec)
- [ ] Gate check passes: `python -m pytest test_ga.py test_modos.py test_registro.py -v`
- [ ] Test count: os 70 testes existentes + 20 de `test_registro.py` passam

**Tests**: integration
**Gate**: full

**Commit**: `feat(cli): watch the latest training by default`

---

### T9: Gráficos de aptidão

**What**: Script `graficos.py`: lê o `fitness.csv` de uma pasta e grava `aptidao.png` e `aptidao_por_frames.png`, sem abrir janela.
**Where**: `graficos.py`
**Depends on**: T8
**Reuses**: matplotlib
**Requirement**: PLOT-01, PLOT-02, PLOT-08, PLOT-09, PLOT-11

**Done when**:

- [ ] `test_grafico_de_aptidao`: `aptidao.png` é gravado; a figura tem as curvas `melhor`, `mediana`, `média` e `pior` com os valores do CSV por geração e uma faixa entre média − desvio e média + desvio
- [ ] `test_grafico_de_aptidao_por_frames`: `aptidao_por_frames.png` é gravado; o eixo x das curvas `melhor` e `média` é a soma acumulada da coluna `frames`
- [ ] `test_graficos_nao_abrem_janela`: sem `--mostrar`, o backend é `agg` e `plt.show` não é chamado
- [ ] `test_pasta_sem_fitness_csv`: imprime `Sem fitness.csv em: <pasta>` e devolve 1
- [ ] `test_csv_sem_geracoes`: só com o cabeçalho, imprime `Sem gerações em: <pasta>` e devolve 1
- [ ] Gate check passes: `python -m pytest test_ga.py test_modos.py test_registro.py -v`
- [ ] Test count: os 70 testes existentes + 25 de `test_registro.py` passam

**Tests**: unit
**Gate**: quick

**Commit**: `feat(plots): fitness charts from a training folder`

---

### T10: Gráficos de mortes, obstáculos e diversidade

**What**: `graficos.py` grava também `mortes.png`, `obstaculos.png` e `diversidade.png`, e pula com aviso os gráficos cujas colunas faltam.
**Where**: `graficos.py`
**Depends on**: T9
**Reuses**: leitura e `main` de T9
**Requirement**: PLOT-03, PLOT-04, PLOT-05, PLOT-10

**Done when**:

- [ ] `test_grafico_de_mortes`: barras empilhadas; a base é `mortes_cacto` e o topo de cada barra é `mortes_cacto + mortes_ptera`
- [ ] `test_grafico_de_obstaculos`: curvas `melhor` e `média` com os valores de `obstaculos_melhor` e `obstaculos_media`
- [ ] `test_grafico_de_diversidade`: uma curva com os valores de `diversidade`
- [ ] `test_csv_antigo_pula_graficos`: com um CSV de 3 colunas, grava só `aptidao.png` (curvas `melhor` e `média`) e imprime `Gráfico pulado, faltam colunas: <arquivo>` para os outros quatro, devolvendo 0
- [ ] Gate check passes: `python -m pytest test_ga.py test_modos.py test_registro.py -v`
- [ ] Test count: os 70 testes existentes + 29 de `test_registro.py` passam

**Tests**: unit
**Gate**: quick

**Commit**: `feat(plots): deaths, obstacles and diversity charts`

---

### T11: Comparação entre treinos e --mostrar

**What**: Com mais de uma pasta, `graficos.py` grava `comparacao.png` na pasta atual; com `--mostrar`, abre os gráficos depois de gravá-los.
**Where**: `graficos.py`
**Depends on**: T10
**Reuses**: leitura e `main` de T9
**Requirement**: PLOT-06, PLOT-07

**Done when**:

- [ ] `test_comparacao_entre_treinos`: com duas pastas, `comparacao.png` é gravado na pasta atual com uma curva de média por treino, rotulada com o nome da pasta, e os cinco gráficos de cada pasta também são gravados; com uma pasta só, `comparacao.png` não é criado
- [ ] `test_mostrar_abre_os_graficos`: com `--mostrar`, `plt.show` é chamado uma vez, depois de os arquivos existirem
- [ ] Gate check passes: `python -m pytest test_ga.py test_modos.py test_registro.py -v`
- [ ] Test count: os 70 testes existentes + 31 de `test_registro.py` passam

**Tests**: unit
**Gate**: quick

**Commit**: `feat(plots): compare runs and optional display`

---

### T12: README atualizado

**What**: O README descreve a pasta `treinos/`, os quatro arquivos de cada treino, as colunas do `fitness.csv`, a opção `--saida`, o novo padrão de `--assistir` e o uso de `graficos.py`.
**Where**: `README.md`
**Depends on**: T11
**Reuses**: seções Uso e O que o treino grava
**Requirement**: nenhum - documentação da feature

**Done when**:

- [ ] Cada comando e nome de arquivo citado no README existe e se comporta como descrito, conferido rodando os comandos em uma pasta temporária
- [ ] Gate check passes: `python -m py_compile AGMLP.py DinoGame.py RedeNeural.py autodino.py; python -m pytest test_ga.py test_modos.py test_registro.py -v`
- [ ] Test count: os 70 testes existentes + 31 de `test_registro.py` passam

**Tests**: none
**Gate**: build

**Commit**: `docs: describe training folders, record columns and plots`

---

## Checks

**C1** - Um treino pela linha de comando cria `treinos/<AAAAMMDD-HHMMSS>_s<semente>` com `fitness.csv` e `bestDino.din` (REC-01, AC 1)
Proof: run unit | test_registro.py::test_treino_cria_pasta_com_data_e_semente PASSED

**C2** - `config.json` é gravado antes da primeira geração com as 13 chaves da spec (REC-02, AC 2)
Proof: run unit | test_registro.py::test_config_json_antes_da_primeira_geracao PASSED

**C3** - `resumo.json` é gravado depois da última geração com as 5 chaves da spec (REC-03, AC 3)
Proof: run unit | test_registro.py::test_resumo_json_no_fim PASSED

**C4** - `--saida DIR` grava o treino em `DIR` (REC-04, AC 4)
Proof: run unit | test_registro.py::test_saida_escolhida PASSED

**C5** - Pasta que já tem `fitness.csv`: `Pasta já tem um treino: <caminho>`, código 1, sem treinar (REC-05, AC 5)
Proof: run unit | test_registro.py::test_pasta_com_treino_e_recusada PASSED

**C6** - `--assistir` sem arquivo carrega o `bestDino.din` do treino mais recente em `treinos/` (REC-06, AC 6)
Proof: run unit | test_registro.py::test_assistir_sem_arquivo_usa_o_treino_mais_recente PASSED

**C7** - `--assistir` sem arquivo e sem treino: `Nenhum treino encontrado em: treinos`, código 1, sem janela (REC-07, AC 7)
Proof: run unit | test_registro.py::test_assistir_sem_nenhum_treino PASSED

**C8** - O cabeçalho do `fitness.csv` é o de 12 colunas da spec (MET-01, AC 1)
Proof: run unit | test_registro.py::test_cabecalho_do_fitness_csv PASSED

**C9** - `mediana`, `desvio` (populacional) e `pior` são os dos scores da geração (MET-02, AC 2)
Proof: run unit | test_registro.py::test_mediana_desvio_e_pior PASSED

**C10** - `frames` é o número de frames simulados na geração (MET-03, AC 3)
Proof: run unit | test_registro.py::test_frames_da_geracao PASSED

**C11** - Obstáculos vencidos por dino: borda direita do obstáculo passou da borda esquerda do dino com ele vivo (MET-04, AC 4)
Proof: run unit | test_registro.py::test_obstaculos_vencidos_por_dino PASSED

**C12** - `mortes_cacto` e `mortes_ptera` contam as mortes por tipo de obstáculo (MET-05, AC 5)
Proof: run unit | test_registro.py::test_mortes_por_tipo_de_obstaculo PASSED

**C13** - `diversidade` é a média, sobre os genes, do desvio padrão de cada gene entre as redes da geração (MET-06, AC 6)
Proof: run unit | test_registro.py::test_diversidade_no_csv PASSED

**C14** - Mesmos N, gerações e semente: `fitness.csv` de 12 colunas idêntico com e sem janela (MET-07, AC 7)
Proof: run unit | test_registro.py::test_csv_completo_igual_com_e_sem_janela PASSED

**C15** - `aptidao.png`: melhor, mediana, média e pior por geração, com faixa de média ± desvio (PLOT-01, AC 1)
Proof: run unit | test_registro.py::test_grafico_de_aptidao PASSED

**C16** - `aptidao_por_frames.png`: melhor e média pelos frames acumulados (PLOT-02, AC 2)
Proof: run unit | test_registro.py::test_grafico_de_aptidao_por_frames PASSED

**C17** - `mortes.png`: mortes por cacto e por ptera em barras empilhadas (PLOT-03, AC 3)
Proof: run unit | test_registro.py::test_grafico_de_mortes PASSED

**C18** - `obstaculos.png`: `obstaculos_melhor` e `obstaculos_media` por geração (PLOT-04, AC 4)
Proof: run unit | test_registro.py::test_grafico_de_obstaculos PASSED

**C19** - `diversidade.png`: diversidade por geração (PLOT-05, AC 5)
Proof: run unit | test_registro.py::test_grafico_de_diversidade PASSED

**C20** - Mais de uma pasta: `comparacao.png` na pasta atual, com a média de cada treino rotulada pelo nome da pasta (PLOT-06, AC 6)
Proof: run unit | test_registro.py::test_comparacao_entre_treinos PASSED

**C21** - `--mostrar` abre os gráficos depois de gravá-los (PLOT-07, AC 7)
Proof: run unit | test_registro.py::test_mostrar_abre_os_graficos PASSED

**C22** - Sem `--mostrar`, nenhum gráfico abre janela (PLOT-08, AC 8)
Proof: run unit | test_registro.py::test_graficos_nao_abrem_janela PASSED

**C23** - Pasta sem `fitness.csv`: `Sem fitness.csv em: <pasta>`, código 1 (PLOT-09, AC 9)
Proof: run unit | test_registro.py::test_pasta_sem_fitness_csv PASSED

**C24** - CSV sem as colunas de um gráfico: grava os demais e imprime `Gráfico pulado, faltam colunas: <arquivo>` (PLOT-10, AC 10)
Proof: run unit | test_registro.py::test_csv_antigo_pula_graficos PASSED

**C25** - Dois treinos com a mesma semente no mesmo segundo: a segunda pasta ganha o sufixo `-2` (REC-08, Edge Case 1)
Proof: run unit | test_registro.py::test_mesmo_segundo_ganha_sufixo PASSED

**C26** - Treino interrompido: `config.json`, `fitness.csv` parcial e `bestDino.din`, sem `resumo.json` (REC-09, Edge Case 2)
Proof: run unit | test_registro.py::test_treino_interrompido_sem_resumo PASSED

**C27** - Sem git: `commit` nulo e `alteracoes_locais` falso (REC-10, Edge Case 3)
Proof: run unit | test_registro.py::test_versao_sem_git PASSED

**C28** - `fitness.csv` sem linhas de dados: `Sem gerações em: <pasta>`, código 1 (PLOT-11, Edge Case 4)
Proof: run unit | test_registro.py::test_csv_sem_geracoes PASSED

---

## Handoff

**Settled mid-build:** 2026-11-23 - execução inline, sem sub-agentes: oferta feita com o plano ("Aprova o plano de tarefas, com execução nesta sessão?"), usuário: "Aprovo, pode executar."
**Dispatched:** none
**Walked:** none

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4

Phase 1:  T1 → T2 → T3 → T4
Phase 2:  T4 → T5 → T6 → T7 → T8
Phase 3:  T8 → T9 → T10 → T11
Phase 4:  T11 → T12
```

12 tarefas: passa do limite de ~8 de um lote. A oferta de sub-agentes vem antes da primeira tarefa.

---

## Task Granularity Check

| Task | Scope | Status |
| ---- | ----- | ------ |
| T1: Diversidade da população | 1 função | ✅ Granular |
| T2: Hiperparâmetros em constantes | 3 constantes em 3 funções | ⚠️ OK, coeso |
| T3: Contadores por dino e por geração | 1 método + 2 atributos | ⚠️ OK, coeso |
| T4: Registro por geração com todas as colunas | 1 função | ✅ Granular |
| T5: Versão do código | 1 função | ✅ Granular |
| T6: Treino grava config, registro completo e resumo | 1 função (`train`) | ✅ Granular |
| T7: Pasta por treino | 1 função (`main`) + 1 linha de `.gitignore` | ⚠️ OK, coeso |
| T8: Assistir o treino mais recente | 1 função (`main`) | ✅ Granular |
| T9: Gráficos de aptidão | 1 arquivo novo: leitura, 2 gráficos, `main` | ⚠️ OK, coeso |
| T10: Gráficos de mortes, obstáculos e diversidade | 3 funções de gráfico | ✅ Granular |
| T11: Comparação entre treinos e --mostrar | 1 função de gráfico + 1 opção | ✅ Granular |
| T12: README atualizado | 1 arquivo | ✅ Granular |

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
| T12 | T11 | T11 → T12 | ✅ Match |

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| ---- | --------------------------- | --------------- | --------- | ------ |
| T1 | Algoritmo genético | unit | unit | ✅ OK |
| T2 | Algoritmo genético | unit | unit | ✅ OK |
| T3 | Laço de treino | integration | integration | ✅ OK |
| T4 | Métricas e registro | unit | unit | ✅ OK |
| T5 | Métricas e registro | unit | unit | ✅ OK |
| T6 | Laço de treino | integration | integration | ✅ OK |
| T7 | Linha de comando | integration | integration | ✅ OK |
| T8 | Linha de comando | integration | integration | ✅ OK |
| T9 | Gráficos | unit | unit | ✅ OK |
| T10 | Gráficos | unit | unit | ✅ OK |
| T11 | Gráficos | unit | unit | ✅ OK |
| T12 | Documentação e configuração | none | none | ✅ OK |
