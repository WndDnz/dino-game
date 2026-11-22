# headless-training-and-watch verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at df1427e
**Verifier**: independent sub-agent (author != verifier)
**After the fix pass**: the 5 findings below are closed by commits. Rows C27-C30 cover checks added in the fix pass and were judged by the author, since the method runs no second Verifier.
**Measurement** (spec Success Criteria, "medição única"): driver `dummy`, 350 dinos alive, median ms per frame - windowed training at ad914bb 16.63 ms (three runs: 17.52, 16.26, 16.63); headless training at df1427e 1.63-1.70 ms; ratio about 10, target 4. Same run at df1427e: windowed 4.45-5.00 ms, ratio 2.7-2.9, target 2.

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `test_modos.py` `test_sem_janela_usa_driver_dummy` | yes |
| C2 | `test_modos.py` `test_mesmo_csv_com_e_sem_janela` | yes |
| C3 | `test_modos.py` `test_imprime_linha_por_geracao` | yes |
| C4 | `test_modos.py` `test_sem_janela_termina_com_codigo_0` | yes |
| C5 | `test_modos.py` `test_sem_janela_metade_do_tempo` | yes |
| C6 | `test_modos.py` `test_pilha_nao_cresce_entre_geracoes` | yes |
| C7 | `test_modos.py` `test_opcoes_de_treino_sao_usadas` | yes |
| C8 | `test_modos.py` `test_sem_janela_interrompido_mantem_melhor` | yes - one completed generation only; the record across generations is held by `test_ga.py` `test_salva_melhor_de_todos` |
| C9 | `test_modos.py` `test_assistir_rede_controla_o_dino_a_60_fps` | yes |
| C10 | `test_modos.py` `test_assistir_carrega_o_arquivo_indicado` | yes |
| C11 | `test_modos.py` `test_assistir_mostra_pontuacao` | yes |
| C12 | `test_modos.py` `test_assistir_usa_regras_do_jogo_manual` | no - asserts the watch track equals `Pista` alone, not the rule values (2 cacti, ptera after 700 frames, speed +1 per 700) |
| C13 | `test_modos.py` `test_assistir_colisao_mostra_fim_de_jogo` | yes |
| C14 | `test_modos.py` `test_assistir_espaco_reinicia_com_a_mesma_rede` | yes |
| C15 | `test_modos.py` `test_assistir_esc_encerra_com_codigo_0` | no - asserts the `SystemExit` of `gameplay()`, not the exit code of the `autodino.py` process |
| C16 | `test_modos.py` `test_assistir_semente_por_partida` | yes |
| C17 | `test_modos.py` `test_assistir_arquivo_inexistente` | yes |
| C18 | `test_modos.py` `test_assistir_arquivo_invalido` | yes |
| C19 | `test_modos.py` `test_sem_opcoes_treina_350_por_30_com_janela` | yes |
| C20 | `test_modos.py` `test_treino_com_janela_desenha_dinos_e_hud` | no - asserts one red and one blue pixel in the HUD band, not the four HUD items |
| C21 | `test_modos.py` `test_tres_modos_mesma_pista` | no - asserts the three logs are equal, not the rule values (2 cacti, ptera 46x40 after 700 frames, speed +1 per 700) |
| C22 | `test_modos.py` `test_obstaculo_novo_a_160_px` | yes |
| C23 | `test_modos.py` `test_sensor_mede_cacto_mais_proximo_a_frente` | yes |
| C24 | `test_modos.py` `test_sensor_vale_1_quando_cactos_passaram` | yes |
| C25 | `test_modos.py` `test_individuos_ou_geracoes_menor_que_1` | yes |
| C26 | `test_modos.py` `test_sem_janela_com_assistir_e_erro` | yes |
| C27 | `test_modos.py` `test_pista_regras_do_jogo_manual` | yes - named as a proof in the fix pass (ffd1082); the Verifier read this test and reported it as the one holding the rule values |
| C28 | `test_modos.py` `test_assistir_processo_sai_com_codigo_0` | yes - added in the fix pass (3d9e657), judged by the author: asserts `returncode == 0` of a new process for ESC and for QUIT |
| C29 | `test_modos.py` `test_semente_fora_da_faixa_e_erro_de_uso` | yes - added in the fix pass (33a18e5), judged by the author: -1, -4 and 4294967296 give exit 2 in the three modes with nothing started; 0 and 4294967295 are accepted |
| C30 | `test_modos.py` `test_assistir_caminho_que_nao_e_arquivo` | yes - added in the fix pass (0e6573c), judged by the author: a directory gives the exact message, exit 1, no window |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| C20 passes with two of the four HUD items missing | `test_modos.py:286-288` - `(255, 0, 0) in hud` and `(0, 0, 255) in hud`; alive and best are both red, senses and score both blue (`DinoGame.py:427-432`), so dropping "Best fitness" or "Senses" keeps the test green | assert each of the four texts: spy on `render_to` and check the four strings, or check pixels inside each of the four rects | e74fc87 and 465a33a - C20 now checks the four HUD areas by colour and the four texts |
| The values of TRACK-01 and WATCH-04 are held by a test no check names | C12 and C21 compare logs between modes that all use the same `Pista`; a third cactus, a 40x40 ptera or a ptera before frame 700 keeps both green. The values are asserted only in `test_modos.py:140-151` `test_pista_regras_do_jogo_manual`, which is in no `Proof:` line | name `test_pista_regras_do_jogo_manual` as a proof of TRACK-01 and WATCH-04 | ffd1082 - C27 names `test_pista_regras_do_jogo_manual` as the proof of the rule values |
| C15 does not run at the process layer the Test Coverage Matrix names for exit codes | `test_modos.py:594-596` and `602-604` assert `SystemExit` raised by `gameplay()`. The path `autodino.py:55` then `autodino.py:68-74` is not run by any test: `gameplay` never returns, `return 0` at `autodino.py:56` is unreachable, and the exit code depends on `except Exception` not catching `SystemExit`. Own run in a new process with driver `dummy`: ESC gives exit 0, QUIT gives exit 0 | add a new-process test: `autodino.py --assistir <file>` with driver `dummy` and ESC (and QUIT) posted, assert `returncode == 0` | 3d9e657 - C28 (`test_assistir_processo_sai_com_codigo_0`) asserts the process return code for ESC and QUIT |
| A negative `--semente` crashes the training with a traceback, exit 1 | own run: `autodino.py --sem-janela --individuos 2 --geracoes 3 --semente -4` prints `ValueError: Seed must be between 0 and 2**32 - 1`, exit 1. `autodino.py:33-37` accepts any integer; `DinoGame.py:451` calls `np.random.seed(semente_base)`. With a window the crash comes after the start screen. No criterion or check names the bounds of `--semente` | new criterion and check: `--semente` outside what `np.random.seed` accepts is a usage error, exit 2, before training | 33a18e5 - CLI-03 added to the spec; C29 (`test_semente_fora_da_faixa_e_erro_de_uso`) |
| `--assistir` with a directory as path prints a traceback and no message | own run: `autodino.py --assistir sprites` prints `PermissionError: [Errno 13] Permission denied: 'sprites'`, exit 1. `autodino.py:47-54` catches only `FileNotFoundError` and `ValueError`; `DinoGame.py:624` opens the path outside the `try` | new criterion and check: a path that cannot be read as a file prints `Arquivo inválido: <caminho>`, exit 1; catch `OSError` in `autodino.py` | 0e6573c - WATCH-11 added to the spec; C30 (`test_assistir_caminho_que_nao_e_arquivo`) |
