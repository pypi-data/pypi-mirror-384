.PHONY: dev install clean test-viewer serve

PORT ?= 3000

dev:
	poetry run python src/server.py

langgraph-dev:
	poetry run langgraph dev

test-viewer:
	@echo "Starting test results QA server at http://localhost:3000/test_results_viewer.html"
	@echo "Accept/Reject buttons will directly update the JSONL file with automatic backups"
	@cd data && python3 qa_server.py 3000

serve:
	@echo "📊 Serving static files at http://localhost:$(PORT)"
	@echo "   Visualization: http://localhost:$(PORT)/src/evaluator/visualization.html"
	@python -m http.server $(PORT)

install:
	poetry install

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete