.PHONY: setup lint test smoke audit reproduce-headline submission

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

reproduce-headline:
	@echo "No validated primary aggregate exists in the starting scaffold."
	@echo "Aarav replaces this guard after the August 7 results freeze."
	@exit 3

submission:
	bash scripts/build_submission.sh
