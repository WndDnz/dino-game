# Training Record and Plots Specification

**Approved**: 2026-11-22 - user: "1. Concordo 2. no próprio fitness.csv 3. OK"

## Problem Statement

Um treino hoje deixa só `fitness.csv` com o melhor score e a média de cada geração, na pasta em que o comando rodou, e o treino seguinte apaga o anterior. Não ficam registrados os hiperparâmetros, a semente nem a versão do código, então dois treinos não podem ser comparados. Faltam também as estatísticas usuais de um trabalho de treino (distribuição da população, custo, métricas da tarefa, diversidade) e uma forma pronta de ver os dados em gráfico.

## Goals

- [ ] Cada treino fica em uma pasta própria, com configuração, métricas por geração, melhor rede e resumo, e nunca é sobrescrito por outro.
- [ ] O registro por geração traz distribuição dos scores, custo em frames, métricas da tarefa e diversidade da população.
- [ ] Um comando gera os gráficos de um treino e a comparação entre vários.
- [ ] O registro continua reproduzível: mesma semente, mesmo `fitness.csv`, com ou sem janela.

## Out of Scope

| Feature | Reason |
| ------- | ------ |
| Avaliação em pistas de teste fixas | Spec separada, pedida pelo usuário |
| Repetir um treino com várias sementes e calcular intervalo de confiança | Depende das pistas de teste para valer a pena; o gráfico de comparação aceita várias pastas, mas não agrega |
| Tempo de relógio por geração no CSV | Tornaria o `fitness.csv` diferente a cada execução e quebraria a reprodutibilidade (HEAD-02); o tempo total vai para `resumo.json` |
| Retomar um treino interrompido | Feature própria |
| Painel ao vivo, TensorBoard ou similar | Os arquivos são CSV e JSON, legíveis por qualquer ferramenta |
| Estatísticas dos pesos e saturação das ativações | Não pedido; a diversidade cobre o caso de convergência prematura |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --------------------- | -------------- | --------- | ---------- |
| Onde cada treino é gravado | Pasta `treinos/<AAAAMMDD-HHMMSS>_s<semente>/`, criada pela linha de comando; a raiz do repositório deixa de receber `fitness.csv` e `bestDino.din` | Um treino não apaga o outro, e o `bestDino.din` versionado para de aparecer como modificado no git | y - usuário: "1. Concordo" |
| `--assistir` sem arquivo | Carrega o `bestDino.din` do treino mais recente em `treinos/` | Com os treinos em pastas, o `bestDino.din` da raiz deixa de ser atualizado. Muda o critério WATCH-02 já aprovado | y - usuário: "1. Concordo" |
| Formato do registro por geração | As colunas novas entram no próprio `fitness.csv`, depois de `geracao,melhor,media` | Um arquivo só. Muda o cabeçalho fixado em LOG-02 e exige atualizar as asserções de cabeçalho e de linhas de dois testes existentes (`test_ga.py` `test_csv_linha_por_geracao`, `test_modos.py` `test_sem_janela_termina_com_codigo_0`) | y - usuário: "2. no próprio fitness.csv" |
| Métricas por geração | `mediana`, `desvio`, `pior`, `frames`, `obstaculos_melhor`, `obstaculos_media`, `mortes_cacto`, `mortes_ptera`, `diversidade` | As linhas de esforço pequeno da lista apresentada ao usuário | y - usuário: "3. OK" |
| Desvio | Desvio padrão populacional dos scores (divisor N) | A geração inteira é medida, não uma amostra | n |
| Obstáculo vencido | Um obstáculo conta para um dino quando a borda direita dele passa da borda esquerda do dino com o dino vivo | Mesma noção de "passou" do sensor de cacto (AD-007) | n |
| Diversidade | Média, sobre os 94 genes, do desvio padrão de cada gene na população avaliada | Simples, barata e cai para 0 quando todos os indivíduos são iguais | n |
| Versão do código | Hash curto do commit e um indicador de alterações locais, obtidos do git; `null` e `false` se o git não estiver disponível | Liga um resultado ao código que o produziu | n |
| Gráficos | Script `graficos.py`, com matplotlib, que grava PNG e não abre janela a não ser com `--mostrar` | matplotlib 3.9.2 já está instalado e é usado por `teste.py` | y - usuário: "3. OK" |
| CSV de treinos antigos | `graficos.py` desenha os gráficos cujas colunas existem e avisa quais pulou | O usuário já tem `fitness.csv` no formato de 3 colunas | n |
| Pasta escolhida que já tem um treino | Erro, sem treinar | Nunca sobrescrever um treino | n |

**Open questions:** none - all resolved or logged above. As linhas com `n` são padrões técnicos escolhidos pelo agente, abertos a correção.

---

## User Stories

### P1: Um registro por treino ⭐ MVP

**User Story**: Como pesquisador, quero que cada treino fique em uma pasta com a configuração que o produziu, para comparar treinos sem perder nenhum.

**Why P1**: Sem isso as métricas novas continuam sendo apagadas pelo treino seguinte.

**Acceptance Criteria**:

1. WHEN um treino é iniciado pela linha de comando THEN o programa SHALL criar a pasta `treinos/<AAAAMMDD-HHMMSS>_s<semente>` e gravar nela `fitness.csv` e `bestDino.din`.
2. WHEN um treino é iniciado pela linha de comando THEN o programa SHALL gravar na pasta do treino, antes da primeira geração, o arquivo `config.json` com `individuos`, `geracoes`, `semente`, `janela`, `topologia`, `taxa_mutacao`, `sigma_mutacao`, `elite`, `torneio`, `alpha_blx`, `commit`, `alteracoes_locais` e `inicio`.
3. WHEN a última geração termina THEN o programa SHALL gravar na pasta do treino o arquivo `resumo.json` com `geracoes_concluidas`, `melhor_score`, `geracao_do_melhor`, `frames_total` e `segundos_total`.
4. WHERE `--saida DIR` é informado, o programa SHALL gravar o treino em `DIR` no lugar da pasta automática.
5. IF a pasta de destino já contém `fitness.csv` THEN o programa SHALL imprimir `Pasta já tem um treino: <caminho>` e encerrar com código de saída 1, sem treinar.
6. WHEN `--assistir` é usado sem arquivo THEN o jogo SHALL carregar o `bestDino.din` da pasta de treino mais recente em `treinos/`.
7. IF `--assistir` é usado sem arquivo e `treinos/` não tem nenhum `bestDino.din` THEN o jogo SHALL imprimir `Nenhum treino encontrado em: treinos` e encerrar com código de saída 1, sem abrir janela.

**Independent Test**: Rodar dois treinos curtos seguidos e ver duas pastas em `treinos/`, cada uma com `config.json`, `fitness.csv`, `bestDino.din` e `resumo.json`; `python autodino.py --assistir` joga com a rede do segundo.

---

### P1: Métricas por geração ⭐ MVP

**User Story**: Como pesquisador, quero a distribuição dos scores, o custo e as métricas da tarefa de cada geração, para entender o que a população está aprendendo.

**Why P1**: É o conteúdo do registro estendido.

**Acceptance Criteria**:

1. WHEN um treino cria o `fitness.csv` THEN a primeira linha SHALL ser `geracao,melhor,media,mediana,desvio,pior,frames,obstaculos_melhor,obstaculos_media,mortes_cacto,mortes_ptera,diversidade`.
2. WHEN uma geração termina THEN o treino SHALL registrar em `mediana`, `desvio` e `pior` a mediana, o desvio padrão populacional e o menor valor dos scores da geração.
3. WHEN uma geração termina THEN o treino SHALL registrar em `frames` o número de frames simulados naquela geração.
4. WHEN uma geração termina THEN o treino SHALL registrar em `obstaculos_melhor` e `obstaculos_media` o maior valor e a média, entre os dinos, do número de obstáculos cuja borda direita passou da borda esquerda do dino enquanto ele estava vivo.
5. WHEN uma geração termina THEN o treino SHALL registrar em `mortes_cacto` e `mortes_ptera` quantos dinos morreram em colisão com cacto e quantos com ptera.
6. WHEN uma geração termina THEN o treino SHALL registrar em `diversidade` a média, sobre os genes, do desvio padrão de cada gene entre as redes avaliadas naquela geração.
7. WHEN dois treinos usam os mesmos indivíduos, gerações e semente, um com janela e outro sem THEN os dois SHALL produzir `fitness.csv` idênticos, com todas as colunas.

**Independent Test**: Treinar 10 dinos por 3 gerações e conferir, linha a linha, que `mortes_cacto + mortes_ptera` é 10 e que `pior <= mediana <= melhor`.

---

### P1: Gráficos ⭐ MVP

**User Story**: Como pesquisador, quero gerar os gráficos de um treino com um comando, para ler o resultado sem montar planilha.

**Why P1**: Pedido explícito do usuário.

**Acceptance Criteria**:

1. WHEN `python graficos.py <pasta>` roda THEN o script SHALL gravar em `<pasta>` o arquivo `aptidao.png` com as curvas de melhor, mediana, média e pior por geração e uma faixa de média ± desvio.
2. WHEN `python graficos.py <pasta>` roda THEN o script SHALL gravar `aptidao_por_frames.png` com as curvas de melhor e média em função dos frames simulados acumulados.
3. WHEN `python graficos.py <pasta>` roda THEN o script SHALL gravar `mortes.png` com as mortes por cacto e por ptera de cada geração em barras empilhadas.
4. WHEN `python graficos.py <pasta>` roda THEN o script SHALL gravar `obstaculos.png` com as curvas de `obstaculos_melhor` e `obstaculos_media` por geração.
5. WHEN `python graficos.py <pasta>` roda THEN o script SHALL gravar `diversidade.png` com a curva de diversidade por geração.
6. WHEN `graficos.py` recebe mais de uma pasta THEN o script SHALL gravar na pasta atual o arquivo `comparacao.png` com a curva de média por geração de cada treino, identificada pelo nome da pasta.
7. WHERE `--mostrar` é informado, o script SHALL abrir os gráficos em janelas depois de gravá-los.
8. The script SHALL gerar os arquivos sem abrir janela quando `--mostrar` não é informado.
9. IF a pasta não contém `fitness.csv` THEN o script SHALL imprimir `Sem fitness.csv em: <pasta>` e encerrar com código de saída 1.
10. IF o `fitness.csv` não tem as colunas de um gráfico THEN o script SHALL gravar os demais e imprimir `Gráfico pulado, faltam colunas: <arquivo>` para cada um que não gerou.

**Independent Test**: Treinar 30 dinos por 5 gerações, rodar `python graficos.py treinos/<pasta>` e abrir os cinco PNG.

---

## Edge Cases

- IF dois treinos com a mesma semente começam no mesmo segundo THEN o programa SHALL criar a segunda pasta com o sufixo `-2`.
- IF o treino é interrompido antes da última geração THEN a pasta SHALL conter `config.json`, o `fitness.csv` das gerações concluídas e o `bestDino.din`, sem `resumo.json`.
- IF o git não está disponível THEN o programa SHALL gravar `commit` como `null` e `alteracoes_locais` como `false`.
- IF `fitness.csv` existe mas não tem nenhuma linha de dados THEN `graficos.py` SHALL imprimir `Sem gerações em: <pasta>` e encerrar com código de saída 1.

---

## Implicit-Requirement Dimensions

| Dimension | Resolution |
| --------- | ---------- |
| Input validation & bounds | Registro, critério 5; gráficos, critérios 9 e 10; edge case 4 |
| Failure / partial-failure states | Edge cases 2 e 3 |
| Idempotency / retry / duplicate handling | Registro, critério 5; edge case 1 |
| Auth boundaries & rate limits | N/A because é um programa local de um usuário |
| Concurrency / ordering | Edge case 1 |
| Data lifecycle / expiry | Registro, critérios 1 e 5: um treino nunca é sobrescrito; apagar pastas antigas é manual |
| Observability | É o assunto da feature |
| External-dependency failure | Edge case 3 (git) |
| State-transition integrity | N/A because não há máquina de estados nova |

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| -------------- | ----- | ----- | ------ |
| REC-01 | P1: Registro (critério 1) | Execute | Verified |
| REC-02 | P1: Registro (critério 2) | Execute | Verified |
| REC-03 | P1: Registro (critério 3) | Execute | Verified |
| REC-04 | P1: Registro (critério 4) | Execute | Verified |
| REC-05 | P1: Registro (critério 5) | Execute | Verified |
| REC-06 | P1: Registro (critério 6) | Execute | Verified |
| REC-07 | P1: Registro (critério 7) | Execute | Verified |
| MET-01 | P1: Métricas (critério 1) | Execute | Verified |
| MET-02 | P1: Métricas (critério 2) | Execute | Verified |
| MET-03 | P1: Métricas (critério 3) | Execute | Verified |
| MET-04 | P1: Métricas (critério 4) | Execute | Verified |
| MET-05 | P1: Métricas (critério 5) | Execute | Verified |
| MET-06 | P1: Métricas (critério 6) | Execute | Verified |
| MET-07 | P1: Métricas (critério 7) | Execute | Verified |
| PLOT-01 | P1: Gráficos (critério 1) | Execute | Verified |
| PLOT-02 | P1: Gráficos (critério 2) | Execute | Verified |
| PLOT-03 | P1: Gráficos (critério 3) | Execute | Verified |
| PLOT-04 | P1: Gráficos (critério 4) | Execute | Verified |
| PLOT-05 | P1: Gráficos (critério 5) | Execute | Verified |
| PLOT-06 | P1: Gráficos (critério 6) | Execute | Verified |
| PLOT-07 | P1: Gráficos (critério 7) | Execute | Verified |
| PLOT-08 | P1: Gráficos (critério 8) | Execute | Verified |
| PLOT-09 | P1: Gráficos (critério 9) | Execute | Verified |
| PLOT-10 | P1: Gráficos (critério 10) | Execute | Verified |
| REC-08 | Edge case 1 | Execute | Verified |
| REC-09 | Edge case 2 | Execute | Verified |
| REC-10 | Edge case 3 | Execute | Verified |
| PLOT-11 | Edge case 4 | Execute | Verified |

**Coverage:** 28 total, 28 mapped to tasks, 0 unmapped.

---

## Sources

- `DinoGame.py:678-695` (`registra_geracao`) - grava `geracao,melhor,media` e a melhor rede em `saida`.
- `DinoGame.py` `train` - recebe `saida="."` e apaga o `fitness.csv` que estiver lá no início de cada treino.
- `autodino.py` - não tem opção de pasta de saída; `--assistir` sem arquivo usa `bestDino.din` da pasta atual.
- `test_ga.py:272` e `test_modos.py:756` - fixam o cabeçalho `geracao,melhor,media`.
- `.specs/features/ga-training-fixes/spec.md` LOG-02 e `.specs/features/headless-training-and-watch/spec.md` HEAD-02 e WATCH-02 - critérios aprovados que esta spec altera ou precisa preservar.
- Estado do repositório em 2026-11-22: `bestDino.din` aparece como modificado e `fitness.csv` como não versionado depois de um treino do usuário na raiz.

---

## Success Criteria

- [ ] Dois treinos seguidos deixam duas pastas completas em `treinos/` e nenhum arquivo novo ou modificado na raiz do repositório.
- [ ] `python graficos.py <pasta>` gera os cinco PNG de um treino de 350 dinos por 30 gerações.
- [ ] Os testes existentes continuam passando, com exceção das duas asserções de cabeçalho, atualizadas para o formato novo.
