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
- **Status**: active

## Handoff

- **Feature**: `.specs/features/ga-training-fixes/` - spec e tasks aprovadas; 11/11 tarefas commitadas
- **Phase / Task**: Execute - verificação; 1 achado do Verifier aberto
- **Completed**: T1-T11; achados 2-5 do Verifier fechados (afd3b92, ca0f22c, 285d3e9, b613ccd)
- **In-progress** (file:line): none
- **Next step**: Usuário decide o achado 1 (meta de 70 redes reativas em 350 não atingida; medido ~8 com `normal(0, 1)`, ~45 com pesos `normal(0, 4)` e bias `normal(0, 1)`). Depois: fechar o achado em `verification.md`, `check_proofs.py`, `validate_verification.py`, lições.
- **Blockers**: decisão do usuário sobre o achado 1
- **Uncommitted files**: none
- **Branch**: master (commits locais, sem push)
