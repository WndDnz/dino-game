# ga-training-fixes verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 29bd2d1
**Verifier**: independent sub-agent (author != verifier)
**After the fix pass**: the 5 findings below are closed by commits. Rows C1 and C22-C24 cover tests written in the fix pass and were judged by the author, since the method runs no second Verifier.

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `test_ga.py` `test_init_pesos_dp4_bias_dp1` | yes - at 29bd2d1 the Verifier judged `test_init_normal_0_1`; the criterion and its test changed in 27037c2 (INIT-02), judged by the author |
| C2 | `test_ga.py` `test_sensores_normalizados` | yes |
| C3 | `test_ga.py` `test_sensor_sem_cacto` | yes |
| C4 | `test_ga.py` `test_sensor_sem_ptera` | yes |
| C5 | `test_ga.py` `test_limiar_05` | no - only 0.51 and 0.49 are tried; `>= 0.5` or `> 0.495` would pass |
| C6 | `test_ga.py` `test_sensores_do_proprio_dino` | yes |
| C7 | `test_ga.py` `test_proxima_geracao_devolve_n` | yes |
| C8 | `test_ga.py` `test_elite_identica` | yes |
| C9 | `test_ga.py` `test_entrada_inalterada` | yes |
| C10 | `test_ga.py` `test_torneio_de_3` | yes |
| C11 | `test_ga.py` `test_mutacao_taxa_1_altera_todos` | yes |
| C12 | `test_ga.py` `test_mutacao_taxa_0_nao_altera` | yes |
| C13 | `test_ga.py` `test_mutacao_delta_normal_0_05` | yes |
| C14 | `test_ga.py` `test_colisoes_mesmo_frame` | yes |
| C15 | `test_ga.py` `test_pulo_sem_mixer` | yes |
| C16 | `test_ga.py` `test_semente_por_geracao` | no - the `random.seed(semente_base + g)` half holds; the "same `fitness.csv`" half passes only because the test helper calls `np.random.seed(0)` itself |
| C17 | `test_ga.py` `test_csv_linha_por_geracao` | yes |
| C18 | `test_ga.py` `test_salva_melhor_de_todos` | yes |
| C19 | `test_ga.py` `test_sem_elite_gera_n_filhos` | no - asserts the count, and "no elite" by `is`, which is false for a deep-copied elite too |
| C20 | `test_ga.py` `test_torneio_populacao_menor_que_3` | yes |
| C21 | `test_ga.py` `test_treino_interrompido_mantem_melhor` | yes |
| C22 | `test_ga.py` `test_elite_proporcional_ao_n_recebido` | yes - added in the fix pass (afd3b92), judged by the author: asserts exactly the 3 top-scored of 30 survive intact, with mutation rate 1.0 |
| C23 | `test_ga.py` `test_treino_semeia_numpy` | yes - added in the fix pass (b613ccd), judged by the author: same `semente_base` gives equal initial populations from different numpy states, another base gives a different one |
| C24 | `test_ga.py` `test_populacao_inicial_reativa` | yes - added in the fix pass (27037c2), judged by the author: counts networks whose jump decision crosses 0.5 over 201 steps of `l`, asserts >= 35 |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| Goal 1 and Success Criterion 1 (at least 70 of 350 initial networks change the "pular" output as `l` goes 1.0 to 0.0) are not met, and no check names them | Own run at HEAD, 350 `RedeNeural((5,8,4,2))`, `l` swept 1.0..0.0 in 201 steps, output 0 compared with 0.5: 11, 11, 8, 20, 7, 7 reactive for `np.random.seed` 0..5 (other sensors `nl=1, na=0, ds=0, s=0.2`); 6 to 16 with three other settings of the fixed sensors. About half the networks always jump and half never do | Add a check with the spec's Independent Test (seeded, count >= 70) and change the initialisation or input scaling until it passes, or have the user lower the target in a new criterion | 27037c2 - user chose weights `normal(0, 4)` and a goal of 35 of 350 ("Aprovo, pode prosseguir."); C24 (`test_populacao_inicial_reativa`) now names the goal, C1 holds the new initialisation (INIT-02, INIT-03, AD-006) |
| A training run is not repeatable with the same `semente_base`: the initial population, crossover and mutation draw from `np.random`, which `train` never seeds | Own run, `train(nIndividuals=10, nGenerations=3, semente_base=0)` twice without seeding numpy: `1,44,21.6 / 2,44,26.6 / 3,44,39.0` against `1,44,24.4 / 2,44,27.2 / 3,44,36.8`. With `np.random.seed(0)` before each run the two files are equal. `test_ga.py:275` seeds numpy in the helper; `DinoGame.py:396` seeds only `random` | Seed `np.random` from `semente_base` at the start of a training in `train`, and drop `np.random.seed(0)` from `_treina` so C16 proves it | b613ccd - C23 (`test_treino_semeia_numpy`) and C16, whose helper no longer seeds numpy |
| C19 does not prove "no elite": the identity assertion can never fail | `test_ga.py:141` uses `r is rede`; the elite is built with `copy.deepcopy` (`AGMLP.py:213`), so a copy of the best network would pass | Assert that no network of the new population has weights and bias equal to an input network (`_iguais`) | ca0f22c - C19 now compares weights and bias |
| C5 does not hold the bound 0.5 | `test_ga.py:199-203` tries 0.51 and 0.49 only. Own run: output exactly 0.5 does not fire and 0.5000001 fires, so the code is right, but `>=` would pass the test | Add the case output == 0.5 does not jump and does not duck | 285d3e9 - C5 now tries output == 0.5 |
| Elite size comes from the constructor's `nIndividuos`, not from the N pairs received (AC 2 fixes `int(N * e)`) | `AGMLP.py:38` `self.tamElite = int(nIndividuos * elite)`. Own run: AG built with `nIndividuos=50, elite=0.1`, 30 pairs passed: 5 networks preserved, criterion gives 3. In `train` the two are equal, so the training is unaffected | Compute the elite size from `len(geracaoAtual)` in `proximaGeracao`, with a test where N differs from `nIndividuos` | afd3b92 - C22 (`test_elite_proporcional_ao_n_recebido`) |
