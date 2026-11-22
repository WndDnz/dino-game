# LESSONS - auto-maintained by scripts/lessons.py

> Machine-owned. Do NOT hand-edit. Changes are overwritten on the next `lessons.py` write.
> Canonical state lives in `.specs/lessons.json`. Edit lessons only via the script.
> promote_threshold=2 distinct features · window_days=45 · quarantine_threshold=2

## Confirmed (load these at Plan/Checks)

Corroborated across multiple features. Safe to apply as guidance.

_none_

## Candidates (under observation - do NOT load as guidance yet)

Seen once or not yet corroborated. Tracked, not trusted.

### L-001 - Give every numeric goal in the spec its own check, and measure the number before writing it
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `spec` · harmful: 0
- features: ga-training-fixes
- evidence: .specs/features/ga-training-fixes/verification.md finding 1 / C24 (spec)
- last seen: 2026-11-22T22:17:13Z

### L-002 - A reproducibility test must not seed the random generators itself; the code under test does the seeding
- signal: `weak_test` · recurrence: 1 feature(s) · scope: `tests` · harmful: 0
- features: ga-training-fixes
- evidence: .specs/features/ga-training-fixes/verification.md finding 2 / C16 (tests)
- last seen: 2026-11-22T22:17:14Z

### L-003 - Compare objects by value, not identity, when the code under test returns copies
- signal: `weak_test` · recurrence: 1 feature(s) · scope: `tests` · harmful: 0
- features: ga-training-fixes
- evidence: .specs/features/ga-training-fixes/verification.md finding 3 / C19 (tests)
- last seen: 2026-11-22T22:17:14Z

### L-004 - Test a strict bound at the bound itself, not only on both sides of it
- signal: `weak_test` · recurrence: 1 feature(s) · scope: `tests` · harmful: 0
- features: ga-training-fixes
- evidence: .specs/features/ga-training-fixes/verification.md finding 4 / C5 (tests)
- last seen: 2026-11-22T22:17:14Z

### L-005 - Derive sizes from the collection received, not from constructor configuration, and test with the two differing
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `ag` · harmful: 0
- features: ga-training-fixes
- evidence: .specs/features/ga-training-fixes/verification.md finding 5 / C22 (ag)
- last seen: 2026-11-22T22:17:14Z

### L-006 - Assert every item a criterion lists, not one representative of the group
- signal: `weak_test` · recurrence: 1 feature(s) · scope: `tests` · harmful: 0
- features: headless-training-and-watch
- evidence: .specs/features/headless-training-and-watch/verification.md finding 1 / C20 (tests)
- last seen: 2026-11-22T23:52:29Z

### L-007 - Give every numeric goal in the spec its own check, and measure the number before writing it
- signal: `weak_test` · recurrence: 1 feature(s) · scope: `spec` · harmful: 0
- features: headless-training-and-watch
- evidence: .specs/features/headless-training-and-watch/verification.md finding 2 / C27 (spec)
- last seen: 2026-11-22T23:52:29Z

### L-008 - Prove an exit code on the process, not on the exception that precedes it
- signal: `weak_test` · recurrence: 1 feature(s) · scope: `tests` · harmful: 0
- features: headless-training-and-watch
- evidence: .specs/features/headless-training-and-watch/verification.md finding 3 / C28 (tests)
- last seen: 2026-11-22T23:52:29Z

### L-009 - Bound every numeric command-line option to the range its consumer accepts
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `cli` · harmful: 0
- features: headless-training-and-watch
- evidence: .specs/features/headless-training-and-watch/verification.md finding 4 / C29 (cli)
- last seen: 2026-11-22T23:52:29Z

### L-010 - Treat a path that exists but is not a readable file as invalid input, not only a missing one
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `cli` · harmful: 0
- features: headless-training-and-watch
- evidence: .specs/features/headless-training-and-watch/verification.md finding 5 / C30 (cli)
- last seen: 2026-11-22T23:52:30Z

## Quarantined (failed when applied - ignore)

A confirmed lesson that recurred alongside failure. Kept for the maintainer to review.

_none_
