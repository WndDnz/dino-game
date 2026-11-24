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
- `matplotlib`, para os gráficos
- `pytest`, só para rodar os testes

```
pip install pygame numpy tqdm matplotlib pytest
```

Rode os comandos a partir da raiz do repositório: os sprites são carregados pelo caminho relativo `sprites/`.

## Uso

| Comando | O que faz |
| --- | --- |
| `python autodino.py` | Treino com janela: tela inicial (ESPAÇO para começar) e depois 350 dinos por 30 gerações |
| `python autodino.py --sem-janela` | Treino sem janela: mais rápido, imprime uma linha por geração e termina sozinho |
| `python autodino.py --assistir` | A melhor rede do treino mais recente em `treinos/` joga sozinha |
| `python autodino.py --assistir outro.din` | Assiste a rede de outro arquivo |
| `python graficos.py treinos/<pasta>` | Gera os gráficos de um treino |
| `python simula_pista.py` | Investiga se as pistas têm situações impossíveis (ver abaixo) |

Opções:

| Opção | Padrão | Vale para |
| --- | --- | --- |
| `--individuos N` | 350 | os dois treinos |
| `--geracoes G` | 30 | os dois treinos |
| `--pistas N` | 5 | os dois treinos: pistas de treino por geração |
| `--semente S` | 0 | treino: semente base; assistir: mesma pista em toda partida |
| `--saida PASTA` | `treinos/<data-hora>_s<semente>` | os dois treinos |

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

Cada treino ganha uma pasta própria, `treinos/<AAAAMMDD-HHMMSS>_s<semente>/`, ou a indicada em `--saida`. Um treino nunca sobrescreve outro: uma pasta que já tem `fitness.csv` é recusada, e dois treinos no mesmo segundo ganham o sufixo `-2`. A pasta `treinos/` está no `.gitignore`.

| Arquivo | Conteúdo |
| --- | --- |
| `config.json` | Indivíduos, gerações, semente, janela, topologia, hiperparâmetros do algoritmo genético, número de pistas de treino e de teste, teto de frames, commit do código e se havia alterações locais, horário de início. Gravado antes da primeira geração |
| `fitness.csv` | Uma linha por geração (colunas abaixo) |
| `bestDino.din` | A melhor rede até o momento, regravada a cada recorde |
| `resumo.json` | Gerações concluídas, melhor fitness, geração em que ele apareceu e o score de teste dessa geração, frames e segundos totais. Gravado depois da última geração; um treino interrompido não tem resumo |

### Pistas de treino e pistas de teste

A mesma rede faz de 105 a 518 pontos conforme a pista, então uma pista só mede mais a sorte que a rede. Por isso:

- **Fitness**: cada dino corre em 5 pistas de treino (`--pistas N` muda o número) e o fitness dele é a média dos scores. As pistas são as mesmas em todas as gerações: sementes `--semente` + 1 até `--semente` + N.
- **Teste**: ao fim de cada geração, a rede de maior fitness corre em 20 pistas de teste, que nunca entram na seleção e são as mesmas em qualquer treino (sementes 900001 a 900020). A média vai para a coluna `teste`. É a medida de generalização, e a que compara dois treinos. Uma `--semente` que faria uma pista de treino coincidir com uma de teste (899981 a 900019, conforme `--pistas`) é recusada com `Semente reservada às pistas de teste`.
- **Teto**: uma partida termina aos 14000 frames (score 2000), mesmo com dinos vivos.

O treino fica cerca de N vezes mais longo que com uma pista. Com janela, as pistas de treino aparecem em sequência e as de teste rodam sem desenho.

Colunas do `fitness.csv`:

| Coluna | Significado |
| --- | --- |
| `geracao` | Número da geração, a partir de 1 |
| `melhor`, `media`, `mediana`, `desvio`, `pior` | Estatísticas dos fitness da geração (média de cada dino nas pistas de treino); o desvio é o populacional |
| `frames` | Frames simulados na geração, somando as pistas de treino (o custo dela) |
| `obstaculos_melhor`, `obstaculos_media` | Obstáculos vencidos por pista, em média: o maior valor e a média entre os dinos |
| `mortes_cacto`, `mortes_ptera` | Quantos dinos morreram em cada tipo de obstáculo, somando as pistas de treino |
| `diversidade` | Média, sobre os genes, do desvio padrão de cada gene na população; cai para 0 quando todos são iguais |
| `teste` | Score médio da melhor rede da geração nas 20 pistas de teste |

O treino é reproduzível: a mesma `--semente` com os mesmos `--individuos`, `--geracoes` e `--pistas` dá o mesmo `fitness.csv`, com ou sem janela. Como a semente padrão é 0, dois treinos sem `--semente` saem iguais; passe outro valor para variar. O tempo de relógio fica só no `resumo.json`, para não quebrar essa garantia.

### Gráficos

```
python graficos.py treinos/<pasta>
python graficos.py treinos/<pasta1> treinos/<pasta2> --mostrar
```

Para cada pasta, grava dentro dela:

| Arquivo | Conteúdo |
| --- | --- |
| `aptidao.png` | Melhor, mediana, média e pior por geração, com a faixa de média ± desvio, e a curva de teste (tracejada) |
| `aptidao_por_frames.png` | Melhor e média pelos frames simulados acumulados |
| `mortes.png` | Mortes por cacto e por ptera em barras empilhadas |
| `obstaculos.png` | Obstáculos vencidos, melhor e média |
| `diversidade.png` | Diversidade da população |

Com mais de uma pasta, grava também `comparacao.png` na pasta atual, com o score de teste por geração de cada treino; se algum deles não tem a coluna `teste`, usa a média. `--mostrar` abre os gráficos depois de gravá-los; sem ele, nada abre janela. Um `fitness.csv` antigo, de 3 colunas, gera só `aptidao.png` e avisa os gráficos pulados; um de 12 colunas gera todos, sem a curva de teste.

Como as pistas de treino são fixas e a elite passa intacta, a linha "melhor" nunca cai de uma geração para a seguinte. Isso vale com 10 indivíduos ou mais: a elite são 10% da população, arredondados para baixo, e com menos de 10 fica vazia. A curva de teste pode cair: é sinal de que a rede está decorando as pistas de treino. Treinos feitos antes das pistas fixas (12 colunas) tinham uma pista diferente por geração e não são comparáveis com os novos.

### Investigar as pistas

```
python simula_pista.py --sementes 50
python simula_pista.py --treino treinos/<pasta> --sementes 50
```

Para cada pista, testa a cada frame todas as combinações de pular e abaixar, com a física e as máscaras de colisão do jogo, e acha o frame em que nenhum dino sobreviveria. Imprime um resumo e grava `pistas.csv` (`--saida` muda o arquivo). Com `--treino`, usa a semente daquele treino: a pista `i` do arquivo é a de semente `--semente` + `i`, ou seja, as primeiras são as pistas de treino dele. Leva alguns segundos por pista.

Resultado de 150 pistas em 2026-11-23: uma não ficou impossível até o score 2000; nas outras 149, a primeira situação sem saída aparece entre os scores 512 e 1904 (mediana 1715), quase sempre com velocidade 20 ou mais, quando um pulo cobre mais chão que o espaço entre obstáculos.

### Avisos

- Os `.din` versionados na raiz são de versões antigas da rede: `--assistir bestDino.din` responde `Arquivo inválido`. Sem arquivo, `--assistir` usa o treino mais recente e responde `Nenhum treino encontrado em: treinos` se ainda não houver nenhum.
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
python -m pytest test_ga.py test_modos.py test_registro.py test_pistas.py -v
```

Rodam sem abrir janela (driver de vídeo `dummy` do SDL) e não gravam nada na raiz do repositório. `test_sem_janela_metade_do_tempo` mede tempo e pode falhar com a máquina ocupada.

## Estrutura

| Caminho | Conteúdo |
| --- | --- |
| `autodino.py` | Linha de comando: os três modos |
| `DinoGame.py` | Jogo, pista, treino, registro, modo assistir |
| `AGMLP.py` | Algoritmo genético |
| `RedeNeural.py` | Rede neural |
| `graficos.py` | Gráficos de um ou mais treinos |
| `simula_pista.py` | Busca exaustiva por situações impossíveis nas pistas |
| `test_ga.py`, `test_modos.py`, `test_registro.py`, `test_pistas.py` | Testes |
| `treinos/` | Um treino por pasta (não versionada) |
| `sprites/` | Imagens e sons do jogo original |
| `.specs/` | Especificações, decisões de projeto (`STATE.md`) e relatórios de verificação de cada feature |
