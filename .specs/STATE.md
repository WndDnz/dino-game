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
- **Status**: active

## Handoff

- **Feature**: `.specs/features/ga-training-fixes/` - spec aprovada em 2026-11-22; `tasks.md` em rascunho, sem aprovação
- **Phase / Task**: Tasks - aguardando aprovação do usuário
- **Completed**: none
- **In-progress** (file:line): none
- **Next step**: Usuário aprova `tasks.md`; então Execute a partir de T1.
- **Blockers**: none (git safe.directory configurado e skill tlc-spec-driven 4.1.0 instalada em 2026-11-22; `validate_spec.py` e `validate_tasks.py` passam)
- **Uncommitted files**: `AGMLP.py`, `DinoGame.py`, `RedeNeural.py`, `autodino.py`, `teste.py` (correções pendentes do usuário, viram o commit de T1); `.specs/`; `graphify-out/`
- **Branch**: master
