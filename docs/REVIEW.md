# Repository review — 2026-11-02

The current GitHub snapshot was materialized and the standard command rerun on Python 3.12/Linux:

```sh
python -m unittest discover -s tests -v
```

All 60 tests pass, covering application functions, file output, CLI behavior and persistence. The README already matches the four applications and their examples; it now links to this repeat verification. No application-code changes were required.

This is a focused regression check, not proof of every input case. Only Python 3.12/Linux was executed here; Python 3.10+ is the declared source target. Existing DESIGN.md documents rounding, duplicate/attempt policies, simplified account records and single-process library persistence.
