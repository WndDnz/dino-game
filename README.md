# dino-game

Estudo de treino de redes neurais com algoritmo genético: uma população de dinossauros aprende a jogar o jogo do T-Rex, cada um controlado por uma pequena rede neural. Não há backpropagation; a pontuação de cada dino é a aptidão que o algoritmo genético usa para gerar a geração seguinte.

## Crédito

O jogo base é o **T-Rex Rush**, de **Shivam Shekhar**: um remake em Python e pygame do jogo do T-Rex do Google Chrome.

- Repositório original: <https://github.com/shivamshekhar/Chrome-T-Rex-Rush> (licença MIT)
- `LICENSE.txt` é a licença do original, copiada sem alteração, com o aviso de copyright de 2016 do autor.
- Deste projeto são o treino por algoritmo genético, a rede neural, a pista compartilhada entre os modos, o modo sem janela e o modo assistir. Os sprites e sons em `sprites/` e a base de `DinoGame.py` vêm do original.

## Requisitos

- Python 3 (testado com 3.11)
- `pygame`, `numpy`, `tqdm`
- `pytest`, só para rodar os testes

```
pip install pygame numpy tqdm pytest
```

Rode os comandos a partir da raiz do repositório: os sprites são carregados pelo caminho relativo `sprites/`.

## Uso

| Comando | O que faz |
| --- | --- |
| `python autodino.py` | Treino com janela: tela inicial (ESPAÇO para começar) e depois 350 dinos por 30 gerações |
| `python autodino.py --sem-janela` | Treino sem janela: mais rápido, imprime uma linha por geração e termina sozinho |
| `python autodino.py --assistir` | A rede salva em `bestDino.din` joga sozinha |
| `python autodino.py --assistir outro.din` | Assiste a rede de outro arquivo |

Opções:

| Opção | Padrão | Vale para |
| --- | --- | --- |
| `--individuos N` | 350 | os dois treinos |
| `--geracoes G` | 30 | os dois treinos |
| `--semente S` | 0 | treino: semente base; assistir: mesma pista em toda partida |

Exemplo: `python autodino.py --sem-janela --individuos 350 --geracoes 100 --semente 7`

O jogo manual, sem rede, não tem opção de linha de comando:

```
python -c "import DinoGame; DinoGame.DinoGame().start()"
```

### Teclas

| Modo | Teclas |
| --- | --- |
| Jogo manual | ESPAÇO pula, ↓ abaixa, Q ou ESC sai |
| Assistir | ESPAÇO ou ENTER recomeça depois do fim de jogo, ESC sai |
| Treino com janela | ESC ou Q sai; → acelera (a tecla ← tem um defeito conhecido) |

### O que o treino grava

Na pasta em que o comando roda:

- `fitness.csv`: uma linha por geração, com `geracao,melhor,media`. É recriado a cada treino.
- `bestDino.din`: a melhor rede até o momento, regravada a cada recorde. Um treino interrompido deixa a melhor das gerações concluídas.

O treino é reproduzível: a mesma `--semente` com os mesmos `--individuos` e `--geracoes` dá o mesmo `fitness.csv`, com ou sem janela. Como a semente padrão é 0, dois treinos sem `--semente` saem iguais; passe outro valor para variar.

### Avisos

- O `bestDino.din` versionado neste repositório é de uma versão antiga da rede. `--assistir` responde `Arquivo inválido: bestDino.din` até um treino regravá-lo. O mesmo vale para os outros `.din` da raiz.
- Os arquivos `.din` são `pickle`: abrir um `.din` de terceiros executa código. Use o modo assistir só com arquivos gerados pelo seu próprio treino.

## Como funciona

**Rede** (`RedeNeural.py`): topologia `(5, 8, 4, 2)`, ativação sigmoide. Pesos iniciados em normal(0, 4) e bias em normal(0, 1).

| Entrada | Significado |
| --- | --- |
| `l` | distância ao cacto mais próximo à frente, dividida pela largura da tela; 1.0 se não há |
| `nl` | distância ao ptera, dividida pela largura; 1.0 se não há |
| `na` | altura da base do ptera, dividida pela altura da tela; 0.0 se não há |
| `ds` | distância entre o cacto e o ptera, dividida pela largura; 0.0 se falta um deles |
| `s` | velocidade da pista dividida por 20 |

As duas saídas são pular e abaixar; cada ação dispara quando a saída passa de 0,5.

**Algoritmo genético** (`AGMLP.py`): a cada geração, os 10% melhores passam intactos (elite); os demais nascem de dois pais escolhidos por torneio de 3, cruzados por BLX-alpha (alpha 0,1), e recebem mutação gaussiana (cada gene soma um valor de normal(0, 0,5) com probabilidade 0,05).

**Pista** (`DinoGame.py`, classe `Pista`): a mesma para o jogo manual, o treino e o modo assistir. Até 2 cactos na tela, ptera depois de 700 frames, velocidade +1 a cada 700 frames, e todo obstáculo novo nasce a pelo menos 160 px dos que já estão na tela.

## Testes

```
python -m pytest test_ga.py test_modos.py -v
```

Rodam sem abrir janela (driver de vídeo `dummy` do SDL) e não gravam nada na raiz do repositório.

## Estrutura

| Caminho | Conteúdo |
| --- | --- |
| `autodino.py` | Linha de comando: os três modos |
| `DinoGame.py` | Jogo, pista, treino, modo assistir |
| `AGMLP.py` | Algoritmo genético |
| `RedeNeural.py` | Rede neural |
| `test_ga.py`, `test_modos.py` | Testes |
| `sprites/` | Imagens e sons do jogo original |
| `.specs/` | Especificações, decisões de projeto (`STATE.md`) e relatórios de verificação de cada feature |
