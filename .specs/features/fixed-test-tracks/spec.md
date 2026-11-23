# Fixed Test Tracks Specification

**Approved**: 2026-11-23 - user: "Aprova"

## Problem Statement

Cada geração corre em uma pista só, diferente da anterior, e o fitness de um indivíduo é o score nessa pista. Medição de 2026-11-23: a mesma rede varia de 105 a 518 pontos conforme a pista (desvio 65), então a curva de fitness oscila com a sorte do sorteio e gerações não são comparáveis entre si. Também não existe uma medida de generalização: nenhuma pista fica fora da seleção para dizer se a melhor rede joga bem em pistas que nunca viu.

## Goals

- [ ] O fitness de cada indivíduo é a média do score em um conjunto fixo de pistas de treino, as mesmas em todas as gerações.
- [ ] A melhor rede de cada geração é medida em um conjunto fixo de pistas de teste, que nunca entra na seleção e é o mesmo em todos os treinos.
- [ ] Os gráficos mostram a curva de teste, e a comparação entre treinos usa essa curva.
- [ ] O registro continua reproduzível: mesma semente e mesmas opções, mesmo `fitness.csv`, com ou sem janela.

## Out of Scope

| Feature | Reason |
| ------- | ------ |
| Sensores novos (segundo obstáculo, estado do dino) e queda rápida | Spec seguinte; esta entrega o instrumento de medida para comparar o antes e o depois |
| Outras topologias de rede | Só se o platô continuar depois dos sensores novos |
| Limitar a velocidade da pista ou descartar pistas que ficam impossíveis | As pistas só ficam impossíveis acima do score 512 (mediana 1715), longe dos cerca de 200 pontos do treino atual |
| Não reavaliar a elite, cujo fitness em pistas fixas não muda | Economiza 10% do tempo; fica para quando o tempo de treino incomodar |
| Vários treinos com sementes diferentes e intervalo de confiança | Feature própria; a curva de teste já torna dois treinos comparáveis |
| Escolher o `bestDino.din` pelo score de teste | As pistas de teste deixariam de ser um conjunto nunca usado em decisão do treino |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --------------------- | -------------- | --------- | ---------- |
| Pistas de treino | As mesmas em todas as gerações | Curva comparável entre gerações; o conjunto de teste mede se a rede decorou as pistas | y - usuário: "Fixas (Recomendado)" |
| Número de pistas de treino | 5 por padrão, opção `--pistas N` | Corta o ruído da pista de 49 para cerca de 22 pontos; o treino fica 5 vezes mais longo | y - usuário: "5 (Recomendado)" |
| Sementes das pistas de treino | `semente + 1` até `semente + N` | Mesma convenção de hoje (`semente + geração`); treinos com `--semente` diferente usam pistas diferentes | n |
| Pistas de teste | 20 pistas, sementes 900001 a 900020, iguais em todo treino e independentes de `--semente` | O score de teste de dois treinos quaisquer fica comparável; 20 pistas dão ruído de cerca de 11 pontos | n |
| Quem corre nas pistas de teste | Só o indivíduo de maior fitness da geração | Custa 20 partidas de um dino por geração; medir a população inteira multiplicaria o tempo por 5 | n |
| Colunas existentes do `fitness.csv` | `melhor`, `media`, `mediana`, `desvio` e `pior` passam a ser calculadas sobre o fitness (média nas pistas de treino); `frames` e as mortes somam as pistas; os obstáculos são a média por pista de cada dino | Um arquivo só, com o mesmo cabeçalho mais uma coluna. Muda o significado das colunas fixado em AD-008 | n |
| Coluna nova | `teste`, no fim do cabeçalho: média do score da melhor rede da geração nas 20 pistas de teste | Uma coluna basta para a curva de generalização | n |
| Teto por pista | Uma partida termina aos 14000 frames (score 2000) com os dinos ainda vivos | Sem teto, uma rede boa prenderia o treino em uma pista; 14000 fica acima do limite físico de quase todas as pistas | n |
| `bestDino.din` | Regravado quando o fitness da melhor rede da geração supera o recorde do treino | Com pistas fixas o fitness é comparável entre gerações, então o recorde deixa de premiar pista fácil | n |
| Treino com janela | Mostra as pistas de treino em sequência, como hoje mostra uma; as pistas de teste rodam sem desenho | Assistir 20 partidas extras por geração não ajuda a acompanhar o treino | n |
| Gráfico de comparação | Usa a coluna `teste` quando todos os treinos comparados a têm; senão, a `media`, como hoje | `media` de treinos com pistas diferentes não é comparável; `teste` é | n |
| `simula_pista.py` | Entra no repositório como ferramenta de investigação, citado no README, sem critérios novos | Foi o que mediu o problema desta spec; hoje está sem commit na raiz | n |

**Open questions:** none - all resolved or logged above. As linhas com `n` são padrões técnicos escolhidos pelo agente, abertos a correção.

---

## User Stories

### P1: Fitness como média em pistas fixas ⭐ MVP

**User Story**: Como pesquisador, quero que cada indivíduo seja avaliado nas mesmas pistas em toda geração, para que o fitness meça a rede e não a sorte da pista.

**Why P1**: É a correção do ruído medido.

**Acceptance Criteria**:

1. WHEN uma geração é avaliada THEN o treino SHALL rodar a população inteira em cada uma das pistas de treino, de sementes `semente + 1` até `semente + N`.
2. WHEN uma geração é avaliada THEN o treino SHALL usar como fitness de cada indivíduo a média dos scores dele nas pistas de treino.
3. The treino SHALL usar as mesmas pistas de treino em todas as gerações.
4. WHERE `--pistas N` é informado, o treino SHALL usar `N` pistas de treino no lugar das 5 padrão.
5. IF `--pistas` recebe um valor menor que 1 ou que não é inteiro THEN o programa SHALL encerrar com código de saída 2, sem treinar.
6. WHEN um dino chega vivo ao frame 14000 de uma pista THEN a partida SHALL terminar com o score que ele tinha nesse frame.
7. WHEN uma geração termina THEN o treino SHALL registrar em `melhor`, `media`, `mediana`, `desvio` e `pior` as estatísticas dos fitness dos indivíduos.
8. WHEN uma geração termina THEN o treino SHALL registrar em `frames`, `mortes_cacto` e `mortes_ptera` a soma dos valores de todas as pistas de treino.
9. WHEN uma geração termina THEN o treino SHALL registrar em `obstaculos_melhor` e `obstaculos_media` o maior valor e a média, entre os dinos, da média por pista de obstáculos vencidos por cada dino.
10. WHEN o fitness do melhor indivíduo de uma geração supera o recorde do treino THEN o treino SHALL regravar `bestDino.din` com essa rede.
11. WHEN um treino é iniciado THEN o `config.json` SHALL trazer também `pistas`, `pistas_teste` e `limite_frames`.

**Independent Test**: Treinar 10 dinos por 3 gerações com `--pistas 3` e conferir, em cada linha, que `mortes_cacto + mortes_ptera` é 30 e que `pior <= mediana <= melhor`.

---

### P1: Pistas de teste ⭐ MVP

**User Story**: Como pesquisador, quero o score da melhor rede em pistas que nunca entram na seleção, para saber se ela generaliza e para comparar treinos.

**Why P1**: Sem o teste, pistas de treino fixas podem ser decoradas sem que ninguém perceba.

**Acceptance Criteria**:

1. WHEN uma geração termina THEN o treino SHALL rodar o indivíduo de maior fitness da geração em cada uma das 20 pistas de teste, de sementes 900001 a 900020.
2. WHEN uma geração termina THEN o treino SHALL registrar em `teste` a média dos scores desse indivíduo nas pistas de teste.
3. WHEN um treino cria o `fitness.csv` THEN a primeira linha SHALL ser `geracao,melhor,media,mediana,desvio,pior,frames,obstaculos_melhor,obstaculos_media,mortes_cacto,mortes_ptera,diversidade,teste`.
4. The treino SHALL selecionar e reproduzir os indivíduos pelo fitness das pistas de treino, sem usar os scores de teste.
5. The pistas de teste SHALL ser as mesmas para qualquer valor de `--semente` e de `--pistas`.
6. WHEN a última geração termina THEN o `resumo.json` SHALL trazer também `teste_do_melhor`, o valor de `teste` da geração em que o recorde foi batido.
7. WHEN uma geração termina em um treino sem janela THEN o programa SHALL imprimir a linha `Geração <g>: melhor=<melhor> media=<media> teste=<teste>`.
8. WHEN dois treinos usam os mesmos indivíduos, gerações, semente e pistas, um com janela e outro sem THEN os dois SHALL produzir `fitness.csv` idênticos, com todas as colunas.

**Independent Test**: Rodar dois treinos curtos com `--semente` diferentes e a mesma rede inicial salva; a coluna `teste` de uma mesma rede é igual nos dois.

---

### P2: Gráficos com a curva de teste

**User Story**: Como pesquisador, quero ver a curva de teste junto da de treino e comparar treinos por ela, para ler generalização sem abrir o CSV.

**Why P2**: O dado já fica no CSV com as histórias P1; o gráfico só facilita a leitura.

**Acceptance Criteria**:

1. WHEN `python graficos.py <pasta>` roda e o `fitness.csv` tem a coluna `teste` THEN o arquivo aptidao.png SHALL trazer também a curva de teste por geração, com a legenda `teste`.
2. WHEN `graficos.py` recebe mais de uma pasta e todas têm a coluna `teste` THEN o arquivo comparacao.png SHALL desenhar a curva de teste de cada treino.
3. IF alguma das pastas comparadas não tem a coluna `teste` THEN o arquivo comparacao.png SHALL desenhar a curva de média de cada treino.
4. IF o `fitness.csv` não tem a coluna `teste` THEN o script SHALL gravar aptidao.png sem a curva de teste e sem imprimir aviso.

**Independent Test**: Rodar `python graficos.py` em um treino novo e em `treinos/20261123-111800_s5` (formato antigo); os dois geram aptidao.png, só o novo com a curva de teste.

---

## Edge Cases

- WHEN `--pistas 1` é informado THEN o treino SHALL usar uma única pista de treino, de semente `semente + 1`, em todas as gerações.
- IF o usuário fecha a janela durante qualquer pista de uma geração THEN o treino SHALL encerrar sem registrar essa geração.
- IF dois indivíduos empatam no maior fitness THEN o treino SHALL escolher o mesmo deles em execuções repetidas com as mesmas opções.

---

## Implicit-Requirement Dimensions

| Dimension | Resolution |
| --------- | ---------- |
| Input validation & bounds | Fitness, critério 5; edge case 1 |
| Failure / partial-failure states | Edge case 2; o treino interrompido continua coberto por REC-09 |
| Idempotency / retry / duplicate handling | Teste, critério 8; edge case 3 |
| Auth boundaries & rate limits | N/A because é um programa local de um usuário |
| Concurrency / ordering | N/A because as pistas rodam em sequência no mesmo processo |
| Data lifecycle / expiry | N/A because não cria arquivos novos; a pasta do treino segue AD-008 |
| Observability | Teste, critérios 2, 6 e 7; gráficos |
| External-dependency failure | N/A because não há dependência externa nova |
| State-transition integrity | Fitness, critério 6 (fim da partida pelo teto) |

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| -------------- | ----- | ----- | ------ |
| FIT-01 | P1: Fitness (critério 1) | - | Pending |
| FIT-02 | P1: Fitness (critério 2) | - | Pending |
| FIT-03 | P1: Fitness (critério 3) | - | Pending |
| FIT-04 | P1: Fitness (critério 4) | - | Pending |
| FIT-05 | P1: Fitness (critério 5) | - | Pending |
| FIT-06 | P1: Fitness (critério 6) | - | Pending |
| FIT-07 | P1: Fitness (critério 7) | - | Pending |
| FIT-08 | P1: Fitness (critério 8) | - | Pending |
| FIT-09 | P1: Fitness (critério 9) | - | Pending |
| FIT-10 | P1: Fitness (critério 10) | - | Pending |
| FIT-11 | P1: Fitness (critério 11) | - | Pending |
| TST-01 | P1: Teste (critério 1) | - | Pending |
| TST-02 | P1: Teste (critério 2) | - | Pending |
| TST-03 | P1: Teste (critério 3) | - | Pending |
| TST-04 | P1: Teste (critério 4) | - | Pending |
| TST-05 | P1: Teste (critério 5) | - | Pending |
| TST-06 | P1: Teste (critério 6) | - | Pending |
| TST-07 | P1: Teste (critério 7) | - | Pending |
| TST-08 | P1: Teste (critério 8) | - | Pending |
| PLOT-12 | P2: Gráficos (critério 1) | - | Pending |
| PLOT-13 | P2: Gráficos (critério 2) | - | Pending |
| PLOT-14 | P2: Gráficos (critério 3) | - | Pending |
| PLOT-15 | P2: Gráficos (critério 4) | - | Pending |
| FIT-12 | Edge case 1 | - | Pending |
| FIT-13 | Edge case 2 | - | Pending |
| TST-09 | Edge case 3 | - | Pending |

**Coverage:** 26 total, 0 mapped to tasks, 26 unmapped.

---

## Sources

- `DinoGame.py` `train` - cada geração chama `random.seed(semente_base + geracao)` e roda uma pista; o fitness é o score nela.
- `DinoGame.py` `roda_geracao` - simula uma pista até todos os dinos morrerem, sem teto de frames.
- `DinoGame.py` `registra_geracao` e `COLUNAS` - 12 colunas fixadas em AD-008; o recorde compara scores de pistas diferentes.
- `graficos.py` - o gráfico de comparação usa a coluna `media`.
- `simula_pista.py` e `treinos/20261123-111800_s5/pistas.csv` - 149 de 150 pistas ficam impossíveis entre os scores 512 e 1904; nenhuma antes disso.
- Medições de 2026-11-23 com a melhor rede do treino `20261123-111800_s5`: score de 105 a 518 em 300 pistas (desvio 65); entre 198 mutantes que funcionam, desvio de 4,4 na qualidade real contra 49 entre pistas.
- `.specs/features/training-record-and-plots/spec.md` MET-01 a MET-07 e PLOT-06 - critérios aprovados que esta spec altera (cabeçalho, significado das colunas, curva da comparação).

---

## Success Criteria

- [ ] Em um treino de 350 dinos por 30 gerações com 5 pistas, a coluna `melhor` nunca diminui de uma geração para a seguinte (a elite é copiada e as pistas são as mesmas).
- [ ] `python graficos.py` em dois treinos novos gera comparacao.png com as curvas de teste.
- [ ] Os testes existentes continuam passando, com as asserções de cabeçalho, de linha impressa e de pista por geração atualizadas para o formato novo.
