# ga-training-fixes proofs

**HEAD**: dc163f3
**Tree**: clean
**Shell**: C:/Program Files/Git\bin\bash.exe
**Result**: 25 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_ga.py::test_init_pesos_dp4_bias_dp1 PASSED` | pass |
| C24 | `run unit / test_ga.py::test_populacao_inicial_reativa PASSED` | pass |
| C2 | `run unit / test_ga.py::test_sensores_normalizados PASSED` | pass |
| C3 | `run unit / test_ga.py::test_sensor_sem_cacto PASSED` | pass |
| C4 | `run unit / test_ga.py::test_sensor_sem_ptera PASSED` | pass |
| C5 | `run unit / test_ga.py::test_limiar_05 PASSED` | pass |
| C6 | `run unit / test_ga.py::test_sensores_do_proprio_dino PASSED` | pass |
| C7 | `run unit / test_ga.py::test_proxima_geracao_devolve_n PASSED` | pass |
| C8 | `run unit / test_ga.py::test_elite_identica PASSED` | pass |
| C22 | `run unit / test_ga.py::test_elite_proporcional_ao_n_recebido PASSED` | pass |
| C9 | `run unit / test_ga.py::test_entrada_inalterada PASSED` | pass |
| C10 | `run unit / test_ga.py::test_torneio_de_3 PASSED` | pass |
| C11 | `run unit / test_ga.py::test_mutacao_taxa_1_altera_todos PASSED` | pass |
| C12 | `run unit / test_ga.py::test_mutacao_taxa_0_nao_altera PASSED` | pass |
| C13 | `run unit / test_ga.py::test_mutacao_delta_normal_0_05 PASSED` | pass |
| C14 | `run unit / test_ga.py::test_colisoes_mesmo_frame PASSED` | pass |
| C15 | `run unit / test_ga.py::test_pulo_sem_mixer PASSED` | pass |
| C16 | `run unit / test_ga.py::test_semente_por_geracao PASSED` | pass |
| C23 | `run unit / test_ga.py::test_treino_semeia_numpy PASSED` | pass |
| C17 | `run unit / test_ga.py::test_csv_linha_por_geracao PASSED` | pass |
| C18 | `run unit / test_ga.py::test_salva_melhor_de_todos PASSED` | pass |
| C19 | `run unit / test_ga.py::test_sem_elite_gera_n_filhos PASSED` | pass |
| C20 | `run unit / test_ga.py::test_torneio_populacao_menor_que_3 PASSED` | pass |
| C21 | `run unit / test_ga.py::test_treino_interrompido_mantem_melhor PASSED` | pass |
| Build | `python -m py_compile AGMLP.py DinoGame.py RedeNeural.py autodino.py` | pass |

## Output

`Run unit` - exit 0

```
test_ga.py::test_sem_elite_gera_n_filhos PASSED                          [ 52%]
test_ga.py::test_sensores_normalizados PASSED                            [ 56%]
test_ga.py::test_sensor_sem_cacto PASSED                                 [ 60%]
test_ga.py::test_sensor_sem_ptera PASSED                                 [ 64%]
test_ga.py::test_sensores_do_proprio_dino PASSED                         [ 68%]
test_ga.py::test_limiar_05 PASSED                                        [ 72%]
test_ga.py::test_pulo_sem_mixer PASSED                                   [ 76%]
test_ga.py::test_colisoes_mesmo_frame PASSED                             [ 80%]
test_ga.py::test_csv_linha_por_geracao PASSED                            [ 84%]
test_ga.py::test_salva_melhor_de_todos PASSED                            [ 88%]
test_ga.py::test_semente_por_geracao PASSED                              [ 92%]
test_ga.py::test_treino_semeia_numpy PASSED                              [ 96%]
test_ga.py::test_treino_interrompido_mantem_melhor PASSED                [100%]

============================= 25 passed in 7.17s ==============================
```
