---
name: Bug report
about: Something behaves differently than the documentation says it does
title: ""
labels: bug
---

**Command run** (verbatim, from the repo root):

```bash

```

**Expected** (quote the README/doc line that sets the expectation):

**Actual** (paste output; include the exit code — measure it unpiped):

**Environment:**

- OS / architecture:
- Python version:
- Install: clean clone + `pip install -e ".[dev]"`? (yes/no)

**Gate state** — output of:

```bash
pytest -q | tail -1
groundtruth steward; echo "rc=$?"
```
