# training-record-and-plots proofs

**HEAD**: 1c81948
**Tree**: dirty - bestDino.din, fitness.csv
**Shell**: C:/Program Files/Git\bin\bash.exe
**Result**: 29 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_registro.py::test_treino_cria_pasta_com_data_e_semente PASSED` | pass |
| C2 | `run unit / test_registro.py::test_config_json_antes_da_primeira_geracao PASSED` | pass |
| C3 | `run unit / test_registro.py::test_resumo_json_no_fim PASSED` | pass |
| C4 | `run unit / test_registro.py::test_saida_escolhida PASSED` | pass |
| C5 | `run unit / test_registro.py::test_pasta_com_treino_e_recusada PASSED` | pass |
| C6 | `run unit / test_registro.py::test_assistir_sem_arquivo_usa_o_treino_mais_recente PASSED` | pass |
| C7 | `run unit / test_registro.py::test_assistir_sem_nenhum_treino PASSED` | pass |
| C8 | `run unit / test_registro.py::test_cabecalho_do_fitness_csv PASSED` | pass |
| C9 | `run unit / test_registro.py::test_mediana_desvio_e_pior PASSED` | pass |
| C10 | `run unit / test_registro.py::test_frames_da_geracao PASSED` | pass |
| C11 | `run unit / test_registro.py::test_obstaculos_vencidos_por_dino PASSED` | pass |
| C12 | `run unit / test_registro.py::test_mortes_por_tipo_de_obstaculo PASSED` | pass |
| C13 | `run unit / test_registro.py::test_diversidade_no_csv PASSED` | pass |
| C14 | `run unit / test_registro.py::test_csv_completo_igual_com_e_sem_janela PASSED` | pass |
| C15 | `run unit / test_registro.py::test_grafico_de_aptidao PASSED` | pass |
| C16 | `run unit / test_registro.py::test_grafico_de_aptidao_por_frames PASSED` | pass |
| C17 | `run unit / test_registro.py::test_grafico_de_mortes PASSED` | pass |
| C18 | `run unit / test_registro.py::test_grafico_de_obstaculos PASSED` | pass |
| C19 | `run unit / test_registro.py::test_grafico_de_diversidade PASSED` | pass |
| C20 | `run unit / test_registro.py::test_comparacao_entre_treinos PASSED` | pass |
| C21 | `run unit / test_registro.py::test_mostrar_abre_os_graficos PASSED` | pass |
| C22 | `run unit / test_registro.py::test_graficos_nao_abrem_janela PASSED` | pass |
| C23 | `run unit / test_registro.py::test_pasta_sem_fitness_csv PASSED` | pass |
| C24 | `run unit / test_registro.py::test_csv_antigo_pula_graficos PASSED` | pass |
| C25 | `run unit / test_registro.py::test_mesmo_segundo_ganha_sufixo PASSED` | pass |
| C26 | `run unit / test_registro.py::test_treino_interrompido_sem_resumo PASSED` | pass |
| C27 | `run unit / test_registro.py::test_versao_sem_git PASSED` | pass |
| C28 | `run unit / test_registro.py::test_csv_sem_geracoes PASSED` | pass |
| Build | `python -m py_compile AGMLP.py DinoGame.py RedeNeural.py autodino.py graficos.py` | pass |

## Output

`Run unit` - exit 0

```
test_registro.py::test_assistir_sem_nenhum_treino[False] PASSED          [ 88%]
test_registro.py::test_assistir_sem_nenhum_treino[True] PASSED           [ 89%]
test_registro.py::test_grafico_de_aptidao PASSED                         [ 90%]
test_registro.py::test_grafico_de_aptidao_por_frames PASSED              [ 91%]
test_registro.py::test_graficos_nao_abrem_janela PASSED                  [ 92%]
test_registro.py::test_pasta_sem_fitness_csv PASSED                      [ 93%]
test_registro.py::test_csv_sem_geracoes PASSED                           [ 94%]
test_registro.py::test_grafico_de_mortes PASSED                          [ 95%]
test_registro.py::test_grafico_de_obstaculos PASSED                      [ 96%]
test_registro.py::test_grafico_de_diversidade PASSED                     [ 97%]
test_registro.py::test_csv_antigo_pula_graficos PASSED                   [ 98%]
test_registro.py::test_comparacao_entre_treinos PASSED                   [ 99%]
test_registro.py::test_mostrar_abre_os_graficos PASSED                   [100%]

============================ 102 passed in 34.93s =============================
```
