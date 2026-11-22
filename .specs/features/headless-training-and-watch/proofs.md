# headless-training-and-watch proofs

**HEAD**: 19ea802
**Tree**: clean
**Shell**: C:/Program Files/Git\bin\bash.exe
**Result**: 31 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_modos.py::test_sem_janela_usa_driver_dummy PASSED` | pass |
| C2 | `run unit / test_modos.py::test_mesmo_csv_com_e_sem_janela PASSED` | pass |
| C3 | `run unit / test_modos.py::test_imprime_linha_por_geracao PASSED` | pass |
| C4 | `run unit / test_modos.py::test_sem_janela_termina_com_codigo_0 PASSED` | pass |
| C5 | `run unit / test_modos.py::test_sem_janela_metade_do_tempo PASSED` | pass |
| C6 | `run unit / test_modos.py::test_pilha_nao_cresce_entre_geracoes PASSED` | pass |
| C7 | `run unit / test_modos.py::test_opcoes_de_treino_sao_usadas PASSED` | pass |
| C8 | `run unit / test_modos.py::test_sem_janela_interrompido_mantem_melhor PASSED` | pass |
| C9 | `run unit / test_modos.py::test_assistir_rede_controla_o_dino_a_60_fps PASSED` | pass |
| C10 | `run unit / test_modos.py::test_assistir_carrega_o_arquivo_indicado PASSED` | pass |
| C11 | `run unit / test_modos.py::test_assistir_mostra_pontuacao PASSED` | pass |
| C12 | `run unit / test_modos.py::test_assistir_usa_regras_do_jogo_manual PASSED` | pass |
| C13 | `run unit / test_modos.py::test_assistir_colisao_mostra_fim_de_jogo PASSED` | pass |
| C14 | `run unit / test_modos.py::test_assistir_espaco_reinicia_com_a_mesma_rede PASSED` | pass |
| C15 | `run unit / test_modos.py::test_assistir_esc_encerra_com_codigo_0 PASSED` | pass |
| C28 | `run unit / test_modos.py::test_assistir_processo_sai_com_codigo_0[pygame.event.Event(pygame.QUIT)] PASSED` | pass |
| C16 | `run unit / test_modos.py::test_assistir_semente_por_partida PASSED` | pass |
| C17 | `run unit / test_modos.py::test_assistir_arquivo_inexistente PASSED` | pass |
| C18 | `run unit / test_modos.py::test_assistir_arquivo_invalido PASSED` | pass |
| C30 | `run unit / test_modos.py::test_assistir_caminho_que_nao_e_arquivo PASSED` | pass |
| C19 | `run unit / test_modos.py::test_sem_opcoes_treina_350_por_30_com_janela PASSED` | pass |
| C20 | `run unit / test_modos.py::test_treino_com_janela_desenha_dinos_e_hud PASSED` | pass |
| C21 | `run unit / test_modos.py::test_tres_modos_mesma_pista PASSED` | pass |
| C27 | `run unit / test_modos.py::test_pista_regras_do_jogo_manual PASSED` | pass |
| C22 | `run unit / test_modos.py::test_obstaculo_novo_a_160_px PASSED` | pass |
| C23 | `run unit / test_modos.py::test_sensor_mede_cacto_mais_proximo_a_frente PASSED` | pass |
| C24 | `run unit / test_modos.py::test_sensor_vale_1_quando_cactos_passaram PASSED` | pass |
| C25 | `run unit / test_modos.py::test_individuos_ou_geracoes_menor_que_1 PASSED` | pass |
| C29 | `run unit / test_modos.py::test_semente_fora_da_faixa_e_erro_de_uso[-1] PASSED` | pass |
| C26 | `run unit / test_modos.py::test_sem_janela_com_assistir_e_erro PASSED` | pass |
| Build | `python -m py_compile AGMLP.py DinoGame.py RedeNeural.py autodino.py` | pass |

## Output

`Run unit` - exit 0

```
test_modos.py::test_assistir_arquivo_invalido PASSED                     [ 82%]
test_modos.py::test_sem_opcoes_treina_350_por_30_com_janela PASSED       [ 84%]
test_modos.py::test_individuos_ou_geracoes_menor_que_1[0---individuos] PASSED [ 85%]
test_modos.py::test_individuos_ou_geracoes_menor_que_1[0---geracoes] PASSED [ 87%]
test_modos.py::test_individuos_ou_geracoes_menor_que_1[-1---individuos] PASSED [ 88%]
test_modos.py::test_individuos_ou_geracoes_menor_que_1[-1---geracoes] PASSED [ 90%]
test_modos.py::test_sem_janela_com_assistir_e_erro PASSED                [ 91%]
test_modos.py::test_assistir_processo_sai_com_codigo_0[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)] PASSED [ 92%]
test_modos.py::test_assistir_processo_sai_com_codigo_0[pygame.event.Event(pygame.QUIT)] PASSED [ 94%]
test_modos.py::test_semente_fora_da_faixa_e_erro_de_uso[-1] PASSED       [ 95%]
test_modos.py::test_semente_fora_da_faixa_e_erro_de_uso[-4] PASSED       [ 97%]
test_modos.py::test_semente_fora_da_faixa_e_erro_de_uso[4294967296] PASSED [ 98%]
test_modos.py::test_assistir_caminho_que_nao_e_arquivo PASSED            [100%]

============================= 70 passed in 23.96s =============================
```
