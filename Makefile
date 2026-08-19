.PHONY: setup lint test smoke audit figures fixture-artifacts validate preflight reproduce-headline submission

setup:
	python -m pip install --require-hashes -r requirements-lock.txt
	python -m pip install -e . --no-deps

lint:
	ruff check .

test:
	pytest -q

smoke:
	python -m human_data_budget.runner.chain --config configs/experiment/toy_cpu.json

audit:
	python scripts/audit_repository.py --strict-structure

# Fixture figures. Output is watermarked non-evidence and must be regenerated
# from immutable chain artifacts before any figure enters the manuscript.
# Requires the `figures` extra: pip install -e ".[figures]"
figures:
	python scripts/generate_figures.py --seeds 5

# Every fixture artifact (figures, tables, CSV, behaviour report) plus a combined
# SHA-256 manifest, from one command. Fixture output only — the real-run
# equivalent is `make reproduce-headline`, which stays guarded until a freeze.
fixture-artifacts:
	python scripts/build_fixture_artifacts.py --seeds 5

# Three-state run validator. Exits 0 valid, 1 valid_with_limitation, 2 invalid,
# 3 usage error. Non-zero for a limitation is deliberate: it must be acknowledged.
# Usage: make validate RUN=results/runs/chain-001
validate:
	python scripts/validate_run.py $(RUN)

# Budget equality check before any chain launches.
# Usage: make preflight CONFIGS="configs/experiment/*.json"
preflight:
	python scripts/preflight_budget.py $(CONFIGS) --compare

reproduce-headline:
	@echo "No validated primary aggregate exists in the starting scaffold."
	@echo "Aarav replaces this guard after the August 7 results freeze."
	@exit 3

submission:
	bash scripts/build_submission.sh
