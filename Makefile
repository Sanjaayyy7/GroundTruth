# The whole gate as one command. `make all` is what CI runs, in CI's order, so
# a green local run and a green pipeline mean the same thing.
.PHONY: all lint typecheck test evidence gate install hooks clean

PY ?= .venv/bin/python
GT ?= $(PY) -m groundtruth.cli

all: gate

install:
	$(PY) -m pip install -e ".[dev]"

hooks: install
	.venv/bin/pre-commit install

lint:
	.venv/bin/ruff check groundtruth tests experiments

typecheck:
	.venv/bin/mypy groundtruth

test:
	$(PY) -m pytest -q

# Regenerates committed evidence. Run it AFTER staging, never before: the
# manifest reads index blobs, so a run before staging describes the previous
# version of the tree. The pre-commit hook exists to enforce that ordering.
evidence:
	$(GT) rescore --check
	$(GT) report
	$(GT) audit
	$(GT) audit --root examples/minijudge --name minijudge
	$(GT) steward

gate: lint typecheck test evidence
	@git diff --exit-code runs/ examples/minijudge/runs/ \
	  && echo "gate: green — committed evidence is byte-fresh" \
	  || (echo "gate: committed evidence is stale; stage and re-run"; exit 1)

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf .mypy_cache .ruff_cache .pytest_cache
