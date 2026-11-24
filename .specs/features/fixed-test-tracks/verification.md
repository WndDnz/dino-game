# Fixed Test Tracks verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 084459b
**Verifier**: independent sub-agent (author != verifier)
**Method**: cada check foi julgado com mutações no código (cerca de 60 implementações erradas, uma por vez, restauradas em seguida) rodando o teste nomeado; as que passaram no teste nomeado foram rodadas contra `test_pistas.py` inteiro ou contra os quatro arquivos. Os exemplos próprios rodaram numa cópia limpa do `HEAD` (`git archive`), fora do repositório. Nenhum arquivo de código ou de teste foi alterado.

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `test_pistas.py` `test_populacao_corre_em_cada_pista_de_treino` | yes - a população inteira e o `random` recém-semeado em cada pista; as sementes `semente + 1` a `semente + N` são seguradas pelos testes de C3, C4 e C24 (com `range(0, pistas)` este teste passa e aqueles três falham) |
| C2 | `test_pistas.py` `test_fitness_e_a_media_das_pistas` | yes - soma, última pista, máximo e score atribuído pela posição em `ranked` falham |
| C3 | `test_pistas.py` `test_mesmas_pistas_em_todas_as_geracoes` | yes |
| C4 | `test_pistas.py` `test_opcao_pistas` | yes - padrão 4, opção ignorada sem janela e opção ignorada com janela falham |
| C5 | `test_pistas.py` `test_pistas_invalido_codigo_2` | yes - aceitar 0 e aceitar 2.5 falham |
| C6 | `test_pistas.py` `test_teto_de_frames` | yes - `<=`, score 0 no teto, vivo contado como morte e constante 14001 falham |
| C7 | `test_pistas.py` `test_estatisticas_sobre_o_fitness` | yes - mediana, desvio amostral e `pior` truncado falham; `melhor` truncado para inteiro passa aqui (o valor do teste é 60.0) e é pego por `test_linha_impressa_com_teste` e por `test_registro.py` |
| C8 | `test_pistas.py` `test_frames_e_mortes_somam_as_pistas` | yes - no nível de `avalia`; o treino gravar as estatísticas das pistas de teste no lugar das de treino é pego pelos testes de C15 e C19 |
| C9 | `test_pistas.py` `test_obstaculos_media_por_pista` | partly - segura a média por pista de cada dino em `avalia`, mas não as colunas `obstaculos_melhor` e `obstaculos_media`; ver findings 1 e 4 |
| C10 | `test_pistas.py` `test_recorde_pelo_fitness` | partly - `>=` falha, mas comparar com o melhor da geração anterior no lugar do recorde do treino passa; ver finding 5 |
| C11 | `test_pistas.py` `test_config_traz_pistas` | yes |
| C12 | `test_pistas.py` `test_melhor_corre_nas_pistas_de_teste` | yes - pior rede, 19 pistas e desempate diferente falham; a asserção `teste[2] is False` é vazia porque o treino do teste já é sem janela (rodar o teste com a janela do treino só é pego, por um `TypeError`, no teste de C25) |
| C13 | `test_pistas.py` `test_coluna_teste_e_a_media` | yes |
| C14 | `test_pistas.py` `test_cabecalho_com_teste` | yes |
| C15 | `test_pistas.py` `test_selecao_ignora_o_teste` | yes - sem repor o `random`, campeã ranqueada pelo score de teste, campeã rebaixada quando o teste é menor que o fitness e rede salva pelo teste falham. Só um valor alternativo de teste é tentado (999.0): subtrair o score de teste do fitness da campeã passa, porque ela cai para o último lugar nos dois treinos |
| C16 | `test_pistas.py` `test_pistas_de_teste_independem_das_opcoes` | yes |
| C17 | `test_pistas.py` `test_resumo_traz_teste_do_melhor` | yes - último teste e maior teste falham |
| C18 | `test_pistas.py` `test_linha_impressa_com_teste` | no - `melhor` e `teste` impressos com uma casa decimal passam; ver finding 6 |
| C19 | `test_pistas.py` `test_csv_igual_com_e_sem_janela_com_pistas` | partly - falha se a janela muda o sorteio ou o teste, mas o treino do teste é curto demais para ver que nem dois treinos sem janela dão o mesmo CSV; ver finding 1 |
| C20 | `test_pistas.py` `test_aptidao_com_curva_de_teste` | yes |
| C21 | `test_pistas.py` `test_comparacao_usa_teste` | yes |
| C22 | `test_pistas.py` `test_comparacao_sem_teste_usa_media` | yes |
| C23 | `test_pistas.py` `test_aptidao_sem_coluna_teste` | yes |
| C24 | `test_pistas.py` `test_uma_pista_so` | yes - mínimo de 2 pistas e a volta a uma pista por geração falham |
| C25 | `test_pistas.py` `test_janela_fechada_nao_registra_geracao` | yes - registrar a geração parcial e sair falha; as implementações que seguem treinando depois do fechamento não falham, travam o teste na tela de fim (sem tempo limite) |
| C26 | `test_pistas.py` `test_empate_no_melhor_e_reproduzivel` | partly - o teste aplica o próprio `max` ao resultado de `avalia`, não a escolha do treino; desempate por `id()` ou pelo último empatado no treino passa aqui e é pego só pelo teste de C12; ver finding 7 |
| C27 | `test_pistas.py` `test_semente_das_pistas_de_teste_e_recusada` | yes - check acrescentado ao fechar o achado 2, depois da rodada do Verifier; julgado pelo autor, não por ele. Cinco implementações erradas falham no teste: sem a recusa na linha de comando, conferindo só a primeira pista, faixa de teste com uma semente a menos, `train` direto sem recusar, outra mensagem |

## Findings

Defeitos de comportamento: 1, 2 e 3. Testes fracos: 4, 5, 6 e 7.

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| 1. Defeito (major). O `fitness.csv` não é reproduzível: `obstaculos_melhor` e `obstaculos_media` mudam entre execuções idênticas, e o valor gravado fica abaixo do real. Quebra a Goal 4, o critério 8 de Teste (TST-08, C19) e a frase "O treino é reproduzível" do README; o critério 9 de Fitness (FIT-09) grava um número errado | `DinoGame.py:367,405-406`: `ja_passaram` guarda `id(o)`; um obstáculo que sai da pista é liberado e o próximo pode nascer com o mesmo `id`, então não é contado. Vem do commit 2536f01 (feature anterior), mas aparece com as pistas fixas porque as redes vão mais longe e correm N pistas. `train(30, 4, semente_base=8, janela=False, pistas=5)` (o comando da caminhada) em 3 processos: geração 4 com `obstaculos_melhor` 5.6, 5.8 e 6.4, três CSVs diferentes. Mantendo os obstáculos vivos numa lista (cópia descartável), todas as execuções dão 7.0 e o mesmo CSV. O teste de C19 passa porque 10 dinos em 3 gerações quase não vencem obstáculos | Guardar em `ja_passaram` o próprio obstáculo, ou marcar um atributo nele, no lugar do `id`. Teste: o mesmo treino duas vezes, com uma população que vença vários obstáculos (30 dinos, 4 gerações, semente 8), dando `fitness.csv` idênticos, e `obstaculos` conferido contra uma contagem independente | 6917f3f - `ja_passaram` guarda o obstáculo; `test_obstaculos_contados_sem_depender_de_id` confere contra uma contagem independente (dava 33 onde o certo era 101) |
| 2. Defeito (minor). Com `--semente` entre 899981 e 900019 as pistas de treino são pistas de teste, e o `teste` deixa de medir generalização sem nenhum aviso. Quebra a Goal 2 ("nunca entra na seleção") e o critério 4 de Teste (TST-04) | `DinoGame.py:554`: sementes de treino `semente + 1` a `semente + N`, sem conferir contra `SEMENTES_TESTE`. `train(12, 3, semente_base=900000, pistas=20)`: `melhor` e `teste` iguais nas três gerações (31.6, 153.35, 157.1). Com `--pistas 5`, as pistas de treino são 900001 a 900005 | Recusar (código 2) ou avisar quando as sementes de treino cruzam as de teste; é um critério novo, a acrescentar na spec com ID e check próprios | a80156f - critério novo TST-10 (C27): `Semente reservada às pistas de teste: <semente>`, código 1, sem treinar; `train` chamado direto levanta `ValueError` antes de gravar |
| 3. Defeito de documentação (minor). O README afirma, sem condição, que "a linha melhor nunca cai de uma geração para a seguinte". Com menos de 10 indivíduos a elite é vazia e `melhor` cai | `AGMLP.py:226`: `tamElite = int(N * 0.1)`. `train(9, 15, semente_base=1, pistas=2)`: `melhor` 110.0 → 22.0 na geração 4, 113.5 → 21.0 na 12. Com elite (40 dinos e 3 pistas, 60 dinos e 5 pistas) nunca caiu, como diz o Success Criterion de 350 dinos | Dizer no README que vale a partir de 10 indivíduos, ou garantir elite mínima de 1 | 4b7bcc7 - o README diz que vale com 10 indivíduos ou mais e explica a elite vazia |
| 4. Teste fraco (C9, FIT-09). Nenhum teste distingue a média da mediana em `obstaculos_media`, e o teste de C9 não lê as colunas do CSV | Trocar `float(np.mean(obstaculos))` por `float(np.median(obstaculos))` em `registra_geracao`: os 129 testes passam. `test_registro.py:211-225` usa `[4, 0, 2]` e `[1, 3, 5, 7]`, em que média e mediana coincidem. `obstaculos_melhor` trocado por `min` é pego só em `test_registro.py` | No teste de C9, treinar com `avalia` fixada em valores assimétricos (por exemplo 0, 5 e 4/3) e conferir `obstaculos_melhor` e `obstaculos_media` na linha do CSV | e619f2c - o teste de C9 treina com obstáculos 0, 0, 0.5 e 8.5 e confere 8.5 e 2.25 no CSV; a mediana agora falha |
| 5. Teste fraco (C10, FIT-10). O teste não distingue o recorde do treino do melhor da geração anterior | Passar `DinoGame.train.currentBest` no lugar de `DinoGame.train.recorde` a `registra_geracao`: os 129 testes passam. A sequência do teste (50, 50, 40, 70.5) não tem uma geração que supere a anterior sem superar o recorde | Acrescentar uma geração assim (por exemplo 50, 40, 45, 70.5) e conferir que `bestDino.din` não é regravado nela e que `geracao_do_melhor` não muda | e619f2c - a sequência ganhou a geração de 45 (supera a anterior, não o recorde); `currentBest` no lugar do recorde agora falha |
| 6. Teste fraco (C18, TST-07). A linha impressa pode arredondar `melhor` e `teste` sem nenhum teste falhar | `teste={teste:.1f}` e `melhor={melhor:.1f}` em `DinoGame.py:582`: os 129 testes passam nos dois casos (`media` com `:.3f` falha). Os valores dos testes têm no máximo uma casa decimal (60.0, 42.5 e os do treino curto) | No caso fixado de `test_linha_impressa_com_teste`, usar um fitness e um teste com mais casas (por exemplo 61.333333333333336 e 42.35) | e619f2c - o caso fixado usa 61.333333333333336 e 42.4375; `:.1f` em `melhor` ou em `teste` agora falha |
| 7. Teste fraco (C26, TST-09). O teste nomeado não exercita a escolha do treino no empate | `max(ranked, key=lambda par: (par[0], id(par[1])))` e `max(reversed(ranked), ...)` em `train`: `test_empate_no_melhor_e_reproduzivel` passa; quem falha é `test_melhor_corre_nas_pistas_de_teste`. O comportamento está certo: com duas redes idênticas no topo (fitness 191.5 nos índices 2 e 4), o treino testou e salvou a de índice 2 nas duas execuções | Fazer o teste de C26 rodar `train` com a população inicial contendo duas cópias da melhor rede e conferir, em duas execuções, que a rede levada ao teste e a salva em `bestDino.din` são a de menor índice | e619f2c - o teste de C26 roda `train` com empate nos índices 1 e 2 e confere, duas vezes, a rede levada ao teste e a salva; o último empatado agora falha |

## Probed without findings

- `--pistas 1` pela linha de comando: uma pista (semente + 1) em toda geração, `config.json` com `pistas` 1; `1.0`, `1e1`, `0x2` e vazio saem com código 2.
- Janela contra sem janela com `--pistas 1`, com 3 pistas e com o teto baixado para 120 frames (todos os dinos vivos no teto, 0 mortes): `fitness.csv` e `bestDino.din` idênticos nos quatro pares.
- O teste não influencia a seleção: trocar `SEMENTES_TESTE` por outras pistas muda só a coluna `teste`; as outras colunas e o `bestDino.din` ficam iguais. O score de uma rede numa pista não depende do resto da população.
- Gráficos com os CSVs antigos de `treinos/`: os de 12 colunas geram os cinco PNG sem aviso e sem curva de teste; o de 3 colunas gera só aptidao.png com os avisos de sempre. Comparação de um treino novo com um de 3 colunas, e com um de 13 colunas com `teste` vazio numa linha, usa a média sem erro.
- Testes anteriores: `git diff 3c1a250..HEAD` em `test_ga.py`, `test_modos.py` e `test_registro.py` só atualiza cabeçalho, linha impressa, sementes e a soma de mortes (10 → 50); nenhum teste removido nem asserção afrouxada.
- Observação, fora dos critérios: com janela, as 20 pistas de teste rodam sem tratar eventos. Uma rede que chegue ao teto nas 20 leva cerca de 16 s por geração (medido com a máquina ocupada) com a janela sem responder.
