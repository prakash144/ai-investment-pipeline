.PHONY: install test run clean

install:
	pip install -r requirements.txt

test:
	PYTHONPATH=. pytest tests/ -v --tb=short

test-cov:
	PYTHONPATH=. pytest tests/ --cov=. --cov-report=term-missing

run:
	PYTHONPATH=. python cli.py --topic "$(topic)" --limit $(limit)

run-default:
	PYTHONPATH=. python cli.py --topic "AI agents for SMBs" --limit 15

clean:
	rm -rf data/candidates data/analysis data/memos data/enrichment reports logs/prompts.jsonl
