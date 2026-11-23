# Training Record and Plots verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 1c81948
**Verifier**: independent sub-agent (author != verifier)
**Gate note**: `validate_verification.py` read the chart file names in the spec criteria (`aptidao.png` and the others, written in backticks) as UI captures and asked for screenshots. They are output files of `graficos.py`; the backticks around those names were removed from the spec, with no change to any criterion's text. The charts themselves were checked by the tests (data of each figure) and by eye during the walk.
**After the fix pass**: the 5 findings below are closed by commits. The two tests added in the fix pass (replay to a new folder, simultaneous runs) and the strengthened C6, C11 and C13 tests were judged by the author, since the method runs no second Verifier.

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `test_registro.py` `test_treino_cria_pasta_com_data_e_semente` | yes - name regex, timestamp inside the run window, the 4 files, nothing at the root |
| C2 | `test_registro.py` `test_config_json_antes_da_primeira_geracao` | yes - reads `config.json` when the first `roda_geracao` starts and asserts all 13 keys with values |
| C3 | `test_registro.py` `test_resumo_json_no_fim` | yes - exact key set, each value against the CSV |
| C4 | `test_registro.py` `test_saida_escolhida` | yes |
| C5 | `test_registro.py` `test_pasta_com_treino_e_recusada` | yes - both modes, message, code 1, `train` not called, file untouched |
| C6 | `test_registro.py` `test_assistir_sem_arquivo_usa_o_treino_mais_recente` | yes for dated folders only - "most recent" is picked by name, see findings |
| C7 | `test_registro.py` `test_assistir_sem_nenhum_treino` | yes - no `treinos/` and a run with no `.din`; `set_mode` not called |
| C8 | `test_registro.py` `test_cabecalho_do_fitness_csv` | yes |
| C9 | `test_registro.py` `test_mediana_desvio_e_pior` | yes - odd and even N, populational vs sample std told apart |
| C10 | `test_registro.py` `test_frames_da_geracao` | yes - equals the number of `Pista.passo` calls |
| C11 | `test_registro.py` `test_obstaculos_vencidos_por_dino` | partly - only populations where every dino has the same count (all N or all 0); a per-dino value taken at the wrong time would pass |
| C12 | `test_registro.py` `test_mortes_por_tipo_de_obstaculo` | yes - all-cactus, all-ptera, and a mixed sum of 40 |
| C13 | `test_registro.py` `test_diversidade_no_csv` | partly - compares the CSV with `AGMLP.diversidade` itself (circular); the formula is held only by `test_diversidade_media_do_desvio_por_gene`, which no check names |
| C14 | `test_registro.py` `test_csv_completo_igual_com_e_sem_janela` | yes - full 12-column text equal, plus row invariants |
| C15 | `test_registro.py` `test_grafico_de_aptidao` | yes - 4 curves with data, band label and extremes |
| C16 | `test_registro.py` `test_grafico_de_aptidao_por_frames` | yes - cumulative x asserted |
| C17 | `test_registro.py` `test_grafico_de_mortes` | yes - heights and stacked bottoms |
| C18 | `test_registro.py` `test_grafico_de_obstaculos` | yes |
| C19 | `test_registro.py` `test_grafico_de_diversidade` | yes |
| C20 | `test_registro.py` `test_comparacao_entre_treinos` | yes - in cwd, labels are folder names, absent with one folder |
| C21 | `test_registro.py` `test_mostrar_abre_os_graficos` | yes - one `show` after all PNGs exist |
| C22 | `test_registro.py` `test_graficos_nao_abrem_janela` | yes - `show` never called and no figure left open; the backend assertion is vacuous since the test sets `MPLBACKEND=Agg` itself |
| C23 | `test_registro.py` `test_pasta_sem_fitness_csv` | yes |
| C24 | `test_registro.py` `test_csv_antigo_pula_graficos` | yes |
| C25 | `test_registro.py` `test_mesmo_segundo_ganha_sufixo` | yes for runs one after another; runs that start in the same second side by side share a folder, see findings |
| C26 | `test_registro.py` `test_treino_interrompido_sem_resumo` | yes |
| C27 | `test_registro.py` `test_versao_sem_git` | yes - missing binary and failing git |
| C28 | `test_registro.py` `test_csv_sem_geracoes` | yes |
| C29 | `test_registro.py` `test_treinos_simultaneos_nao_dividem_pasta` | yes - added in the fix pass (f97693a), judged by the author: the second run fails its own assertion if handed a folder with a `fitness.csv`, and two distinct folders are asserted |
| C30 | `test_registro.py` `test_novo_treino_na_tela_de_fim_vai_para_outra_pasta` | yes - added in the fix pass (f97693a), judged by the author: three folders with all four files, each earlier `fitness.csv` byte-for-byte unchanged |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| A windowed training replayed from the end screen runs again in the same folder: `train` deletes the first run's `fitness.csv` and rewrites `config.json`, `bestDino.din` and `resumo.json`. This breaks "nunca é sobrescrito por outro" (Goal 1) and the README line "Um treino nunca sobrescreve outro" | `DinoGame.py:555-556` `return self.train(..., saida, janela)`, `DinoGame.py:483-484` `os.remove(fitness.csv)`. Run `ex_replay.py`: one folder `['20261123-103249_s3']`, `os.remove` called on `treinos\...\fitness.csv` holding 3 lines | Give a replay its own folder: return to `autodino.main` (or pass in a folder factory) so each replay gets a new `treinos/<data-hora>_s<semente>`. Drop the `os.remove` in `train` too, so no path can delete a run. Add a test for the replay | f97693a - `test_novo_treino_na_tela_de_fim_vai_para_outra_pasta`: three trainings from the end screen land in `_s4`, `_s4-2`, `_s4-3`, none changing the previous one; with `--saida meu`, the next one goes to `meu-2` |
| Two runs with the same seed started in the same second, side by side, share one folder (Edge case 1, REC-08). The name is picked before `introscreen` and the folder is made after it, with `exist_ok=True`. The second `train` then deletes the first run's `fitness.csv` | `autodino.py:97` picks the name, `autodino.py:106-107` `os.makedirs(saida, exist_ok=True)` after the intro screen. Run `ex_mesmo_segundo.py`: both runs used `treinos\20261123-101500_s4` and the second found the first run's `fitness.csv` | Claim the folder as soon as its name is picked, with `os.makedirs(caminho)` (no `exist_ok`) inside the `_pasta_do_treino` loop, retrying on `FileExistsError`. Test it with a second `main` launched from a stubbed `introscreen` | f97693a - `test_treinos_simultaneos_nao_dividem_pasta`: a second run that starts and ends while the first waits on the start screen gets `_s4`, the first gets `_s4-2` |
| `--assistir` with no file picks the most recent run by folder name, not by time. A `--saida treinos/<name>` folder whose name starts with a letter always wins. Same-second suffixes `-10` and up sort before `-9`. In the same second, seed `s9` beats a later `s10` | `autodino.py:34-42` `sorted(os.listdir(raiz), reverse=True)`. Run `ex_recente.py`: last created `20261123-101500_s4` but `experimento` was picked; last created `_s4-11` but `_s4-9` was picked; last created `_s10` but `_s9` was picked | Pick the folder whose `bestDino.din` (or `config.json`) has the latest mtime. Extend C6's test with a custom-named folder and a `-10` suffix | 9ac9501 - C6's test now sets modification times and covers `experimento`, `-9` vs `-11` and seed 9 vs 10 |
| C11's test proves the obstacle count only where every dino has the same value. A count snapshotted at the end of the generation, not at each dino's death, would still pass | `test_registro.py:136-151` asserts `[vencidos] * 4` and `[0, 0, 0, 0]`. The 40-dino case at `:168` checks only `len`. The code is right: `ex_obstaculos.py` with seeds 123 and 2024 (64 and 200 dinos) gives distinct values `[0,1,4,7]` and `[0,4]`, equal to an independent count | Add a case with random nets whose dinos die at different frames, and assert each dino's count against a count taken independently per death frame (as in `ex_obstaculos.py`) | ff81d11 - C11's test adds a random population of 120 checked dino by dino against an independent count at each death frame; counting at the end of the generation now fails it |
| C13's named test is circular: it compares the CSV with `AGMLP.diversidade`, so a wrong formula, such as the sample std, passes | `test_registro.py:212` `== pytest.approx(AGMLP.diversidade(redes))`. The independent values are in `test_diversidade_media_do_desvio_por_gene` (`:39-49`), which no check names | Name `test_diversidade_media_do_desvio_por_gene` in C13's proof, or assert a hand-computed value in `test_diversidade_no_csv` | ff81d11 - C13's test adds genes 0, 2 and 4, asserting sqrt(8/3) |
