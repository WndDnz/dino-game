# fixed-test-tracks proofs

**HEAD**: 1c72170
**Tree**: clean
**Shell**: C:/Program Files/Git\bin\bash.exe
**Result**: 28 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_pistas.py::test_populacao_corre_em_cada_pista_de_treino PASSED` | pass |
| C2 | `run unit / test_pistas.py::test_fitness_e_a_media_das_pistas PASSED` | pass |
| C3 | `run unit / test_pistas.py::test_mesmas_pistas_em_todas_as_geracoes PASSED` | pass |
| C4 | `run unit / test_pistas.py::test_opcao_pistas PASSED` | pass |
| C5 | `run unit / test_pistas.py::test_pistas_invalido_codigo_2 PASSED` | pass |
| C6 | `run unit / test_pistas.py::test_teto_de_frames PASSED` | pass |
| C7 | `run unit / test_pistas.py::test_estatisticas_sobre_o_fitness PASSED` | pass |
| C8 | `run unit / test_pistas.py::test_frames_e_mortes_somam_as_pistas PASSED` | pass |
| C9 | `run unit / test_pistas.py::test_obstaculos_media_por_pista PASSED` | pass |
| C10 | `run unit / test_pistas.py::test_recorde_pelo_fitness PASSED` | pass |
| C11 | `run unit / test_pistas.py::test_config_traz_pistas PASSED` | pass |
| C12 | `run unit / test_pistas.py::test_melhor_corre_nas_pistas_de_teste PASSED` | pass |
| C13 | `run unit / test_pistas.py::test_coluna_teste_e_a_media PASSED` | pass |
| C14 | `run unit / test_pistas.py::test_cabecalho_com_teste PASSED` | pass |
| C15 | `run unit / test_pistas.py::test_selecao_ignora_o_teste PASSED` | pass |
| C16 | `run unit / test_pistas.py::test_pistas_de_teste_independem_das_opcoes PASSED` | pass |
| C17 | `run unit / test_pistas.py::test_resumo_traz_teste_do_melhor PASSED` | pass |
| C18 | `run unit / test_pistas.py::test_linha_impressa_com_teste PASSED` | pass |
| C19 | `run unit / test_pistas.py::test_csv_igual_com_e_sem_janela_com_pistas PASSED` | pass |
| C20 | `run unit / test_pistas.py::test_aptidao_com_curva_de_teste PASSED` | pass |
| C21 | `run unit / test_pistas.py::test_comparacao_usa_teste PASSED` | pass |
| C22 | `run unit / test_pistas.py::test_comparacao_sem_teste_usa_media PASSED` | pass |
| C23 | `run unit / test_pistas.py::test_aptidao_sem_coluna_teste PASSED` | pass |
| C24 | `run unit / test_pistas.py::test_uma_pista_so PASSED` | pass |
| C25 | `run unit / test_pistas.py::test_janela_fechada_nao_registra_geracao PASSED` | pass |
| C26 | `run unit / test_pistas.py::test_empate_no_melhor_e_reproduzivel PASSED` | pass |
| C27 | `run unit / test_pistas.py::test_semente_das_pistas_de_teste_e_recusada PASSED` | pass |
| Build | `python -m py_compile AGMLP.py DinoGame.py RedeNeural.py autodino.py graficos.py simula_pista.py` | pass |

## Output

`Run unit` - exit 0

```
test_pistas.py::test_selecao_ignora_o_teste PASSED                       [ 90%]
test_pistas.py::test_pistas_de_teste_independem_das_opcoes PASSED        [ 91%]
test_pistas.py::test_resumo_traz_teste_do_melhor PASSED                  [ 92%]
test_pistas.py::test_linha_impressa_com_teste PASSED                     [ 93%]
test_pistas.py::test_csv_igual_com_e_sem_janela_com_pistas PASSED        [ 93%]
test_pistas.py::test_opcao_pistas PASSED                                 [ 94%]
test_pistas.py::test_pistas_invalido_codigo_2 PASSED                     [ 95%]
test_pistas.py::test_aptidao_com_curva_de_teste PASSED                   [ 96%]
test_pistas.py::test_aptidao_sem_coluna_teste PASSED                     [ 96%]
test_pistas.py::test_comparacao_usa_teste PASSED                         [ 97%]
test_pistas.py::test_comparacao_sem_teste_usa_media PASSED               [ 98%]
test_pistas.py::test_obstaculos_contados_sem_depender_de_id PASSED       [ 99%]
test_pistas.py::test_semente_das_pistas_de_teste_e_recusada PASSED       [100%]

======================= 132 passed in 117.52s (0:01:57) =======================
```
