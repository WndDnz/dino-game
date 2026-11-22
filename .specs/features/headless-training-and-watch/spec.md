# Headless Training and Watch Specification

**Approved**: 2026-11-22 - user: "1. Sim, atualize o treino. 2. Ok."

## Problem Statement

O treino só roda com janela, desenhando 350 dinos e o HUD a cada frame, e o tempo de uma geração é limitado pelo desenho e por cálculos repetidos por dino. Medido em 2026-11-22: 8,7 ms por frame só de lógica com 350 dinos vivos (115 frames/s), contra 1,3 ms num protótipo com as redes calculadas em lote e máscaras de colisão em cache. Além disso, nada no projeto carrega o `bestDino.din`: não há como ver a rede treinada jogar. E o jogo manual às vezes cria um ptera em cima de um cacto, um obstáculo sem saída.

## Goals

- [ ] Treinar sem abrir janela, com o mesmo resultado do treino com janela para a mesma semente.
- [ ] Com 350 dinos vivos, o treino sem janela processa um frame em no máximo 1/2 do tempo do treino com janela da mesma versão, e em no máximo 1/4 do tempo do treino com janela de antes desta feature (commit ad914bb).
- [ ] Assistir a rede salva em `bestDino.din` jogando, com um comando.
- [ ] O treino com janela continua funcionando como hoje.
- [ ] Nenhuma pista gera um ptera em cima de um cacto.

## Out of Scope

| Feature | Reason |
| ------- | ------ |
| Retomar um treino a partir de uma população salva | Feature própria; hoje só a melhor rede é salva |
| Treino em vários processos ou em GPU | O ganho medido em lote já cobre a meta; complexidade sem necessidade |
| Gráfico do `fitness.csv` | O CSV abre em qualquer planilha |
| Assistir vários dinos ou comparar redes lado a lado | Não pedido |
| Migrar os `.din` anteriores a AD-005 | Decisão já tomada: não são compatíveis |
| Validar a origem do `.din` | O arquivo é `pickle`: abrir um `.din` de terceiros executa código. O modo assistir é para arquivos gerados pelo próprio treino |
| Teclas ← e → do treino com janela (`FPS *= accel`) | Controle de visualização, bug conhecido, não afeta estas duas funcionalidades |
| Remover `SGD`/`backprop`/`AGT`, `acasala0`/`acasala2` e os arquivos `AGMLP`, `np`, `profile` | Limpeza; feature própria |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --------------------- | -------------- | --------- | ---------- |
| Como iniciar cada modo | Opções de linha de comando em `autodino.py`: sem opção = treino com janela (como hoje); `--sem-janela` = treino sem janela; `--assistir [arquivo]` = assistir, com `bestDino.din` como padrão | Um só ponto de entrada, que já existe | y - usuário: "1. ok" |
| Parâmetros do treino | `--individuos` (padrão 350), `--geracoes` (padrão 30), `--semente` (padrão 0), válidos para os dois modos de treino | São os valores fixos hoje em `autodino.py` e em `train` | y - usuário: "1. ok" |
| Pista do modo assistir | As regras do jogo manual: até 2 cactos na tela, ptera depois de 700 frames, velocidade +1 a cada 700 frames | Escolha do usuário, contra a recomendação inicial de usar a pista do treino | y - usuário: "Vamos tentar usar o jogo manual com até 2 cactos" |
| Semente no modo assistir | Pista diferente a cada partida; com `--semente S`, a mesma pista em toda partida | Ver a rede em pistas novas mostra se ela generalizou | y - usuário: "3. ok" |
| Fim de uma partida no modo assistir | Tela de fim de jogo; ESPAÇO ou ENTER inicia outra partida; ESC ou fechar a janela encerra | Mesmo comportamento do jogo manual | y - usuário: "3. ok" |
| Equivalência entre os modos de treino | Mesma semente, mesmos N e gerações: `fitness.csv` idêntico com e sem janela | É a prova de que o treino sem janela simula o mesmo jogo | y - usuário: "3. ok" |
| Saída no terminal do treino sem janela | Uma linha por geração: `Geração <g>: melhor=<score> media=<media>` | Sem janela, é o único sinal de progresso | y - usuário: "3. ok" |
| Meta de velocidade | Teste automático: razão de 2 vezes contra o treino com janela da mesma versão. Medição única: 4 vezes contra o treino com janela do commit ad914bb | A mudança também acelera o treino com janela (medido: 4,9 ms contra 1,3 ms, razão 3,7), então a razão de 4 na mesma execução não é atingível; contra o código anterior a razão medida é 9,2 | y - usuário: "2. Sim" |
| Chamada recursiva de `train` | Vira laço de gerações | Sem janela, treinos longos estouram a pilha: cada geração hoje empilha uma chamada | y - usuário: "3. ok" |
| Ptera em cima de cacto | Um obstáculo novo só nasce quando o anterior já está a pelo menos 160 px; vale para o jogo manual, o modo assistir e o treino | Problema relatado pelo usuário: "Às vezes, vem um ptera em cima de um cacto". Causa: quando não resta cacto na tela, `gameplay` cria um cacto na borda sem olhar onde está o ptera que acabou de nascer. As outras regras de criação já garantem 166 px ou mais | y - usuário: "2. Ok." |
| Pista do treino | As mesmas regras do jogo manual: uma pista só para jogo manual, treino e assistir | A rede é treinada com um cacto por vez; assistida numa pista com 2 cactos, enfrenta uma situação que nunca viu | y - usuário: "1. Sim, atualize o treino." |
| Sensor de cacto com 2 cactos | Mede o cacto mais próximo que ainda não passou pelo dino; se todos já passaram, vale 1.0 como quando não há cacto | Hoje o sensor fica negativo depois que o cacto passa e não sabe escolher entre dois | n |
| Tamanho do ptera | 46x40 em todos os modos | É o do jogo manual; o treino usa 40x40 | n |

**Open questions:** none - all resolved or logged above. As linhas com `n` são padrões técnicos escolhidos pelo agente, abertos a correção.

---

## User Stories

### P1: Treino sem janela ⭐ MVP

**User Story**: Como pesquisador, quero treinar sem abrir janela e mais rápido, para rodar mais gerações e comparar hiperparâmetros em menos tempo.

**Why P1**: É o que destrava experimentos longos; hoje o treino roda no ritmo do desenho.

**Acceptance Criteria**:

1. WHEN `autodino.py` é iniciado com `--sem-janela` THEN o treino SHALL rodar com o driver de vídeo `dummy`, sem abrir janela.
2. WHEN dois treinos usam os mesmos `--individuos`, `--geracoes` e `--semente`, um com janela e outro sem THEN os dois SHALL produzir `fitness.csv` idênticos.
3. WHEN uma geração termina no treino sem janela THEN o treino SHALL imprimir a linha `Geração <g>: melhor=<score> media=<media>`.
4. WHEN a última geração termina no treino sem janela THEN o processo SHALL encerrar com código de saída 0, sem esperar tecla.
5. WHILE 350 dinos estão vivos, o treino sem janela SHALL processar um frame em no máximo 1/2 do tempo que o treino com janela leva, os dois medidos na mesma execução com driver `dummy`. (Era 1/4; alterado em 2026-11-22 - usuário: "2. Sim")
6. WHEN o treino passa de uma geração para a seguinte THEN o treino SHALL manter a mesma profundidade de pilha de chamadas.
7. WHEN `--individuos`, `--geracoes` ou `--semente` são informados THEN o treino SHALL usar esses valores no lugar de 350, 30 e 0.

**Independent Test**: `python autodino.py --sem-janela --individuos 10 --geracoes 2` termina sozinho, imprime 2 linhas de geração e deixa `fitness.csv` com 2 linhas de dados.

---

### P1: Assistir o melhor dino ⭐ MVP

**User Story**: Como pesquisador, quero ver a rede salva jogando, para avaliar o comportamento que o treino produziu.

**Why P1**: O resultado do treino hoje é um arquivo que nada abre.

**Acceptance Criteria**:

1. WHEN `autodino.py` é iniciado com `--assistir` THEN o jogo SHALL abrir a janela com um único dino controlado pela rede de `bestDino.din`, a 60 frames por segundo.
2. WHEN `--assistir` recebe um caminho THEN o jogo SHALL carregar a rede desse arquivo.
3. WHILE a partida corre, o jogo SHALL mostrar a pontuação do dino na tela.
4. WHILE a partida corre, o jogo SHALL gerar os obstáculos pelas regras do jogo manual: até 2 cactos na tela, ptera depois de 700 frames e velocidade +1 a cada 700 frames.
5. WHEN o dino colide com um obstáculo THEN o jogo SHALL parar a partida e mostrar a tela de fim de jogo.
6. WHILE a tela de fim de jogo está visível, WHEN o usuário aperta ESPAÇO ou ENTER THEN o jogo SHALL iniciar outra partida com a mesma rede.
7. WHEN o usuário aperta ESC ou fecha a janela THEN o jogo SHALL encerrar com código de saída 0.
8. WHERE `--semente S` é informado, o jogo SHALL chamar `random.seed(S)` no início de cada partida.
9. IF o arquivo indicado não existe THEN o jogo SHALL imprimir `Arquivo não encontrado: <caminho>` e encerrar com código de saída 1, sem abrir janela.
10. IF o arquivo não contém uma `RedeNeural` de topologia `(5, 8, 4, 2)` THEN o jogo SHALL imprimir `Arquivo inválido: <caminho>` e encerrar com código de saída 1, sem abrir janela.

**Independent Test**: Treinar 2 gerações, rodar `python autodino.py --assistir` e ver um dino jogando sozinho, com a pontuação subindo, até colidir; ESPAÇO recomeça, ESC fecha.

---

### P1: Treino com janela preservado ⭐ MVP

**User Story**: Como pesquisador, quero continuar podendo ver o treino acontecer, para acompanhar a população visualmente.

**Why P1**: É o modo que existe hoje; as mudanças de estrutura não podem quebrá-lo.

**Acceptance Criteria**:

1. WHEN `autodino.py` é iniciado sem opções THEN o jogo SHALL mostrar a tela inicial e, depois dela, treinar 350 dinos por 30 gerações com janela.
2. WHILE o treino com janela corre, o jogo SHALL desenhar os dinos vivos e o HUD com vivos, melhor score da geração anterior, sensores e pontuação.

**Independent Test**: `python autodino.py`, ESPAÇO na tela inicial, e o treino aparece com os dinos e o HUD.

---

### P1: Pista única, sem obstáculo impossível ⭐ MVP

**User Story**: Como jogador e pesquisador, quero que a pista nunca crie um ptera em cima de um cacto e que treino e jogo usem as mesmas regras, para que toda situação tenha saída e a rede seja vista na pista em que treinou.

**Why P1**: O modo assistir passa a usar a pista do jogo manual, que tem esse defeito.

**Acceptance Criteria**:

1. The jogo manual, o treino e o modo assistir SHALL gerar obstáculos pelas mesmas regras: até 2 cactos na tela, ptera de 46x40 depois de 700 frames e velocidade +1 a cada 700 frames.
2. WHEN um obstáculo é criado THEN a borda esquerda dele SHALL ficar a pelo menos 160 px da borda direita de todo obstáculo que já está na tela.
3. WHEN há mais de um cacto na tela THEN o sensor de distância ao cacto SHALL medir o cacto mais próximo cuja borda direita ainda não passou da borda esquerda do dino.
4. IF a borda direita de todos os cactos na tela já passou da borda esquerda do dino THEN o sensor de distância ao cacto SHALL valer 1.0.

**Independent Test**: Simular 20 pistas de 5000 frames com sementes diferentes, sem desenhar, e conferir a menor distância entre obstáculos consecutivos.

---

## Edge Cases

- IF `--individuos` ou `--geracoes` é menor que 1 THEN o programa SHALL imprimir uma mensagem de erro de uso e encerrar com código de saída 2, sem treinar.
- IF `--sem-janela` e `--assistir` são informados juntos THEN o programa SHALL imprimir uma mensagem de erro de uso e encerrar com código de saída 2.
- IF o treino sem janela é interrompido antes da última geração THEN `bestDino.din` SHALL conter a melhor rede das gerações concluídas.
- IF `--semente` é menor que 0 ou maior que 4294967295 THEN o programa SHALL imprimir uma mensagem de erro de uso e encerrar com código de saída 2, sem treinar nem abrir partida. (Acrescentado na verificação: fora dessa faixa `np.random.seed` quebrava o treino com traceback.)

---

## Implicit-Requirement Dimensions

| Dimension | Resolution |
| --------- | ---------- |
| Input validation & bounds | Edge cases 1 e 2; assistir, critérios 9 e 10 |
| Failure / partial-failure states | Edge case 3 |
| Idempotency / retry / duplicate handling | N/A because cada treino recria `fitness.csv` e não há operação repetível parcial |
| Auth boundaries & rate limits | N/A because é um programa local de um usuário |
| Concurrency / ordering | N/A because roda em um processo e uma thread |
| Data lifecycle / expiry | N/A because os arquivos (`fitness.csv`, `bestDino.din`) seguem as regras já definidas em `ga-training-fixes` |
| Observability | Treino sem janela, critério 3 |
| External-dependency failure | N/A because não há serviço externo |
| State-transition integrity | Assistir, critérios 5, 6 e 7: jogando → fim de jogo → jogando ou encerrado |
| Input validation & bounds (pista) | Pista única, critério 2 |

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| -------------- | ----- | ----- | ------ |
| HEAD-01 | P1: Treino sem janela (critério 1) | Tasks | In Tasks |
| HEAD-02 | P1: Treino sem janela (critério 2) | Tasks | In Tasks |
| HEAD-03 | P1: Treino sem janela (critério 3) | Tasks | In Tasks |
| HEAD-04 | P1: Treino sem janela (critério 4) | Tasks | In Tasks |
| HEAD-05 | P1: Treino sem janela (critério 5) | Tasks | In Tasks |
| HEAD-06 | P1: Treino sem janela (critério 6) | Tasks | In Tasks |
| HEAD-07 | P1: Treino sem janela (critério 7) | Tasks | In Tasks |
| WATCH-01 | P1: Assistir (critério 1) | Tasks | In Tasks |
| WATCH-02 | P1: Assistir (critério 2) | Tasks | In Tasks |
| WATCH-03 | P1: Assistir (critério 3) | Tasks | In Tasks |
| WATCH-04 | P1: Assistir (critério 4) | Tasks | In Tasks |
| WATCH-05 | P1: Assistir (critério 5) | Tasks | In Tasks |
| WATCH-06 | P1: Assistir (critério 6) | Tasks | In Tasks |
| WATCH-07 | P1: Assistir (critério 7) | Tasks | In Tasks |
| WATCH-08 | P1: Assistir (critério 8) | Tasks | In Tasks |
| WATCH-09 | P1: Assistir (critério 9) | Tasks | In Tasks |
| WATCH-10 | P1: Assistir (critério 10) | Tasks | In Tasks |
| WIN-01 | P1: Treino com janela (critério 1) | Tasks | In Tasks |
| WIN-02 | P1: Treino com janela (critério 2) | Tasks | In Tasks |
| TRACK-01 | P1: Pista única (critério 1) | Tasks | In Tasks |
| TRACK-02 | P1: Pista única (critério 2) | Tasks | In Tasks |
| TRACK-03 | P1: Pista única (critério 3) | Tasks | In Tasks |
| TRACK-04 | P1: Pista única (critério 4) | Tasks | In Tasks |
| CLI-01 | Edge case 1 | Tasks | In Tasks |
| CLI-02 | Edge case 2 | Tasks | In Tasks |
| HEAD-08 | Edge case 3 | Tasks | In Tasks |
| CLI-03 | Edge case 4 (acrescentado na verificação) | Tasks | In Tasks |

**Coverage:** 26 total, 26 mapped to tasks, 0 unmapped.

---

## Sources

- Medição de 2026-11-22, treino atual com driver `dummy`, 350 dinos, 600 frames: 108 frames/s, com 107 dinos vivos em média. Tempo por função: `pygame.mask.from_surface` 29% (a máscara é refeita a cada teste de colisão), texto do HUD 25%, `feedForward` 19%.
- Medição de 2026-11-22, 350 dinos vivos, só lógica: hoje 8,68 ms por frame (colisão 3,31 ms, rede 5,17 ms, `Dino.update` 0,24 ms); protótipo com redes em lote e máscaras em cache 1,33 ms por frame, 6,5 vezes mais rápido.
- `DinoGame.py` `train` - simulação, desenho e controle de gerações no mesmo laço; uma chamada recursiva por geração.
- `DinoGame.py:274-302` (`gameplay`) - com `len(cacti) == 0` o cacto nasce na borda sem checar o último obstáculo; se esse último é um ptera recém-criado, os dois ficam sobrepostos.
- `autodino.py` - chama `start(nIndividuals=350, nGenerations=30, train=True)`; `start(auto=True)` hoje só chama `gameplay`.
- `RedeNeural.load_object` - existe e não é usado.
- `.specs/STATE.md` AD-004 (persistência por `pickle`) e AD-006 (contrato da rede).

---

## Success Criteria

- [ ] `python autodino.py --sem-janela --individuos 350 --geracoes 30` termina sem intervenção e deixa `fitness.csv` com 30 linhas de dados.
- [ ] Com 350 dinos vivos, um frame do treino sem janela custa no máximo 1/2 de um frame do treino com janela (teste automático).
- [ ] Medição única, registrada na verificação: um frame do treino sem janela custa no máximo 1/4 de um frame do treino com janela do commit ad914bb (medido antes: 12,3 ms).
- [ ] `python autodino.py --assistir` mostra a rede salva jogando.
- [ ] Os 25 testes de `ga-training-fixes` continuam passando.
