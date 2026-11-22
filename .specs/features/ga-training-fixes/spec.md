# GA Training Fixes Specification

**Approved**: 2026-11-22 - user: "1. Inclua 2. Estão bons"

## Problem Statement

O treino por algoritmo genético (`DinoGame.train` + `AGMLP.RNA_AG` + `RedeNeural`) parte de uma população quase inútil e evolui com operadores defeituosos. Medição com 350 redes sintéticas (2026-11-22): 328 nunca pulam, 20 pulam sempre e só 2 reagem ao cacto; 100% dos neurônios da primeira camada saturam; a mutação nunca troca o sinal de um peso; a elite não é garantida. O resultado do experimento hoje depende mais da sorte da população inicial do que do AG.

## Goals

- [ ] A população inicial tem redes que reagem aos sensores: pelo menos 35 das 350 redes mudam a decisão de pular conforme a distância ao cacto varia. (Meta original de 20% trocada em 2026-11-22 depois da medição do Verifier - usuário: "Aprovo, pode prosseguir.")
- [ ] Cada geração tem exatamente N indivíduos, com os `tamElite` melhores preservados sem alteração.
- [ ] O fitness de cada dino depende só da rede dele, não do áudio nem da ordem da lista.
- [ ] A lógica do AG e da rede roda em teste automatizado sem abrir janela.

## Out of Scope

| Feature | Reason |
| ------- | ------ |
| Treino sem renderização e cálculo de todas as redes em um único produto matricial | Feature própria; exige separar simulação e desenho em `DinoGame.py` |
| Modo "assistir o melhor dino" carregando `bestDino.din` | Feature própria; `autodino.py` hoje só treina |
| Compatibilidade com os `.din` existentes | Usuário aceitou a perda (AD-005) |
| Trocar a topologia `(5, 8, 4, 2)` ou adicionar sensores | Não é correção; muda o experimento |
| Recursão de `train()` a cada geração e recarga de sprites por `Dino` | Custo de memória e tempo, não altera o resultado do treino; vai com a feature de treino sem renderização |
| Tecla ← que zera ou nega o FPS (`DinoGame.py:456-458`) | Controle de visualização, não afeta o AG |
| Remover `SGD`/`backprop`/`AGT`, `acasala0`/`acasala2` e os arquivos `AGMLP`, `np`, `profile` da raiz | Limpeza; não muda o resultado do treino |
| Escolha do cacto mais próximo e criação do ptera sem cacto | Verificado: em `train` há no máximo 1 cacto na tela e o ptera entra no jogo ao ser criado; não são bugs |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --------------------- | -------------- | --------- | ---------- |
| Inicialização dos pesos e bias | `np.random.normal(0, 1)` | `normal(-10, 10)` é média −10 e desvio 10; gera 85% de pesos negativos e 94% de redes que nunca pulam | y - usuário: "Pode reescrever a spec." (em resposta à recomendação de incluir inicialização e normalização) |
| Inicialização revista | Pesos `np.random.normal(0, 4)`, bias `np.random.normal(0, 1)`; meta de redes reativas 35 em 350 | Medição de 2026-11-22: `normal(0, 1)` dá ~8 redes reativas em 350; pesos com desvio 4 dão ~45. Em um treino real de 100 dinos e 12 gerações, a média da população foi de 26 a 145 com desvio 4 e ficou entre 21 e 45 com desvio 1 | y - usuário: "Aprovo, pode prosseguir." |
| Normalização dos sensores | Distâncias `l`, `nl`, `ds` divididas por `DinoGame.width`; altura `na` por `DinoGame.height`; velocidade `s` dividida por 20 | Sensores em pixels saturam a sigmoide e anulam a influência da velocidade | y - mesma resposta |
| `.din` antigos | Deixam de ser carregáveis com sentido; nenhum código de migração | Mudou o significado das entradas (AD-005) | y - mesma resposta |
| Valor do sensor sem obstáculo | `l = 1.0` e `nl = 1.0` (obstáculo "na borda da tela"); `na = 0.0`; `ds = 0.0` | Hoje vale 0, igual a "obstáculo colado no dino" | n |
| Limiar de ação | Saída > 0.5 dispara a ação (hoje 0.99) | Com entradas normalizadas a sigmoide deixa de saturar; 0.5 é o ponto médio | y - usuário: "1. Inclua 2. Estão bons" |
| Operador de mutação | Cada gene (peso ou bias) recebe `+ N(0, 0.5)` com probabilidade `taxaMutacao` | O atual só encolhe o peso e nunca troca o sinal | y - usuário: "1. Inclua 2. Estão bons" |
| `taxaMutacao` em `train` | 0.05 (hoje 0.01) | A rede tem 94 genes; com 0.01, 39% dos filhos saem sem mutação | y - usuário: "1. Inclua 2. Estão bons" |
| Tamanho do torneio | 3 indivíduos, fixo (hoje 20% da população = 70) | Com 70, 35% dos pais vêm do top 10 | y - usuário: "1. Inclua 2. Estão bons" |
| Semente da pista | `random.seed(semente_base + geração)` no início de cada geração; `semente_base = 0` por padrão em `train` | Pista reproduzível entre execuções, diferente entre gerações | y - usuário: "1. Inclua 2. Estão bons" |
| Arquivo de log | `fitness.csv` na raiz, colunas `geracao,melhor,media`, uma linha por geração, recriado a cada treino | Não existe registro do progresso além do `print` | n |
| Executor dos testes | `python -m pytest test_ga.py -v`, um arquivo `test_ga.py` na raiz, modo sem janela (`SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`) | pytest 9.0.2 já instalado; projeto não tem testes hoje | n - confirmado na aprovação das tasks |

**Open questions:** none - all resolved or logged above. As histórias P2 entram nesta spec (usuário: "1. Inclua"). As linhas com `n` são padrões técnicos escolhidos pelo agente, abertos a correção.

---

## User Stories

### P1: População inicial reativa ⭐ MVP

**User Story**: Como pesquisador, quero que as redes iniciais respondam aos sensores, para que o AG tenha variação de comportamento para selecionar.

**Why P1**: É o maior limitante medido; sem isso os demais consertos atuam sobre 2 redes úteis em 350.

**Acceptance Criteria**:

1. WHEN uma `RedeNeural` é criada THEN a rede SHALL sortear cada peso e cada bias de uma distribuição normal de média 0 e desvio padrão 1. (Substituído pelo critério 7 em 2026-11-22 - usuário: "Aprovo, pode prosseguir.")
2. WHEN `train` monta o vetor de sensores THEN o treino SHALL entregar `l`, `nl` e `ds` divididos por `DinoGame.width`, `na` dividido por `DinoGame.height` e `s` dividido por 20.
3. IF não há cacto na tela THEN o treino SHALL entregar `l = 1.0`.
4. IF não há ptera na tela THEN o treino SHALL entregar `nl = 1.0`, `na = 0.0` e `ds = 0.0`.
5. WHEN a saída de uma ação é maior que 0.5 THEN o treino SHALL disparar essa ação.
6. WHEN o treino calcula os sensores de um dino THEN o treino SHALL medir as distâncias a partir do `rect` desse mesmo dino.
7. WHEN uma `RedeNeural` é criada THEN a rede SHALL sortear cada peso de uma normal de média 0 e desvio padrão 4 e cada bias de uma normal de média 0 e desvio padrão 1.
8. WHEN 350 redes `(5, 8, 4, 2)` são criadas com semente fixa THEN pelo menos 35 delas SHALL mudar a decisão de pular (saída "pular" cruza 0.5) quando `l` varia de 1.0 a 0.0 com `nl = 1.0`, `na = 0.0`, `ds = 0.0` e `s = 0.2`.

**Independent Test**: Criar 350 redes com semente fixa, variar `l` de 1.0 a 0.0 e contar quantas mudam a saída "pular"; conferir média e desvio dos pesos.

---

### P1: Operadores genéticos corretos ⭐ MVP

**User Story**: Como pesquisador, quero seleção, elitismo e mutação que façam o que o nome diz, para que o fitness por geração reflita o algoritmo.

**Why P1**: Sem elite garantida e com mutação que só encolhe, o gráfico de fitness não diz nada sobre o AG.

**Acceptance Criteria**:

1. WHEN `proximaGeracao` recebe N pares `(score, rede)` THEN o AG SHALL devolver exatamente N redes.
2. WHEN `proximaGeracao` roda com `elite = e` THEN o AG SHALL incluir na nova população `int(N * e)` redes com pesos e bias idênticos aos das `int(N * e)` de maior score.
3. WHEN `proximaGeracao` termina THEN o AG SHALL deixar inalterados os pesos e bias de todas as redes recebidas.
4. WHEN `selecao` roda THEN o AG SHALL escolher cada pai não elite como o de maior score entre 3 indivíduos sorteados.
5. WHEN `aplicaMutacao` roda com `taxaMutacao = 1.0` THEN o AG SHALL alterar todos os pesos e todos os bias da rede.
6. WHEN `aplicaMutacao` roda com `taxaMutacao = 0.0` THEN o AG SHALL deixar a rede inalterada.
7. WHEN `aplicaMutacao` altera um gene THEN o AG SHALL somar a ele um valor sorteado de uma normal de média 0 e desvio padrão 0.5.

**Independent Test**: População sintética com scores conhecidos, sem pygame; no critério 7, média dos deltas de 1000 genes entre −0.1 e 0.1 e pelo menos um delta de cada sinal.

---

### P1: Fitness independente do ambiente ⭐ MVP

**User Story**: Como pesquisador, quero que o score de cada dino dependa só da rede dele, para que a seleção premie o genoma certo.

**Why P1**: Sem áudio nenhum dino pula, e a remoção durante a iteração atrasa mortes.

**Acceptance Criteria**:

1. WHEN vários dinos colidem no mesmo frame THEN o treino SHALL registrar `(score, rede)` de cada um exatamente uma vez e remover todos da lista de vivos nesse frame.
2. WHEN a rede de um dino no chão dispara "pular" THEN o dino SHALL receber velocidade vertical `-jumpSpeed`, com ou sem mixer de áudio inicializado.

**Independent Test**: `Dino` e `Cactus` instanciados com `SDL_VIDEODRIVER=dummy` e `SDL_AUDIODRIVER=dummy`, mixer desligado.

---

### P2: Treino reproduzível e registrado

**User Story**: Como pesquisador, quero repetir um treino e ver o progresso em arquivo, para comparar hiperparâmetros.

**Why P2**: Não corrige comportamento errado, mas sem isso não há como medir o efeito dos consertos P1 no jogo real.

**Acceptance Criteria**:

1. WHEN `train` inicia a geração `g` THEN o treino SHALL chamar `random.seed(semente_base + g)` antes de criar o primeiro obstáculo.
2. WHEN uma geração termina THEN o treino SHALL acrescentar a `fitness.csv` uma linha `geracao,melhor,media` com os scores daquela geração.
3. WHEN uma geração termina com um score maior que todos os anteriores do treino THEN o treino SHALL salvar essa rede em `bestDino.din`.
4. WHEN `train` inicia um treino THEN o treino SHALL chamar `np.random.seed(semente_base)` antes de criar a população inicial.

**Independent Test**: Rodar 2 gerações com N = 10 em modo dummy duas vezes com a mesma semente e comparar os dois `fitness.csv`.

---

## Edge Cases

- IF `int(N * elite)` é 0 THEN o AG SHALL gerar N filhos por crossover, sem elite.
- IF a população tem menos de 3 indivíduos THEN o AG SHALL fazer o torneio com todos os indivíduos.
- IF o treino é encerrado antes da última geração THEN o treino SHALL deixar em `bestDino.din` a melhor rede das gerações concluídas.

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| -------------- | ----- | ----- | ------ |
| INIT-01 | P1: População inicial reativa (critério 1) | - | Superseded by INIT-02 |
| INIT-02 | P1: População inicial reativa (critério 7) | Execute | Implementing |
| INIT-03 | P1: População inicial reativa (critério 8) | Execute | Implementing |
| SENS-01 | P1: População inicial reativa (critério 2) | Execute | Implementing |
| SENS-02 | P1: População inicial reativa (critério 3) | Execute | Implementing |
| SENS-03 | P1: População inicial reativa (critério 4) | Execute | Implementing |
| SENS-04 | P1: População inicial reativa (critério 5) | Execute | Implementing |
| SENS-05 | P1: População inicial reativa (critério 6) | Execute | Implementing |
| AGT-01 | P1: Operadores genéticos (critério 1) | Execute | Implementing |
| AGT-02 | P1: Operadores genéticos (critério 2) | Execute | Implementing |
| AGT-03 | P1: Operadores genéticos (critério 3) | Execute | Implementing |
| AGT-04 | P1: Operadores genéticos (critério 4) | Execute | Implementing |
| MUT-01 | P1: Operadores genéticos (critério 5) | Execute | Implementing |
| MUT-02 | P1: Operadores genéticos (critério 6) | Execute | Implementing |
| MUT-03 | P1: Operadores genéticos (critério 7) | Execute | Implementing |
| FIT-01 | P1: Fitness independente (critério 1) | Execute | Implementing |
| FIT-02 | P1: Fitness independente (critério 2) | Execute | Implementing |
| LOG-01 | P2: Treino reproduzível (critério 1) | Execute | Implementing |
| LOG-02 | P2: Treino reproduzível (critério 2) | Execute | Implementing |
| LOG-03 | P2: Treino reproduzível (critério 3) | Execute | Implementing |
| LOG-04 | P2: Treino reproduzível (critério 4) - acrescentado na verificação: população, crossover e mutação usam `np.random`, que o treino não semeava | Execute | Implementing |

**Coverage:** 21 total, 20 mapped to tasks, 1 superseded (INIT-01), 0 unmapped.

---

## Sources

- Medição de 2026-11-22 com população sintética de 350 redes, sem pygame, fitness por proxy (distância de pulo ao cacto): 85% dos pesos negativos; 328 redes nunca pulam, 20 sempre, 2 reativas; 100% da primeira camada saturada; `selecao` devolve 700 índices; 16 dos 35 slots de elite eram elite; 0 sinais trocados após 20 000 mutações; 33% dos indivíduos alterados por mutação.
- `RedeNeural.py:11-15` - `np.random.normal(-10.0, 10.0)` em pesos e bias.
- `DinoGame.py:496-512` - sensores em pixels, 0 quando falta obstáculo, medidos a partir da variável `dino` que sobrou de outro laço.
- `DinoGame.py:530-540` - limiar 0.99; `dino.movement[1] = -jumpSpeed` dentro do `if pygame.mixer.get_init()`.
- `DinoGame.py:462-471`, `479-488` - `self.dinoArray.remove(d)` dentro de `for d in self.dinoArray`.
- `DinoGame.py:643-658` - `bestDino.din` salvo só depois da última geração; nenhum registro em arquivo.
- `AGMLP.py:63-88` - `selecao` anexa elite + torneio duas vezes; torneio de `int(N * 0.2)`.
- `AGMLP.py:215-226` - `acasalaPppulacao` trata `pais[:tamElite]` como elite depois do embaralhamento.
- `AGMLP.py:228-252` - mutação por multiplicação, aplicada no próprio objeto.
- `.specs/STATE.md` AD-005 - novo contrato de entrada e saída da rede.

---

## Success Criteria

- [ ] Com semente fixa, pelo menos 35 das 350 redes iniciais mudam a decisão de pular quando `l` vai de 1.0 a 0.0.
- [ ] A rede de maior score de cada geração reaparece com pesos e bias idênticos na geração seguinte.
- [ ] Os testes dos 18 requisitos rodam sem janela, em menos de 10 s.
