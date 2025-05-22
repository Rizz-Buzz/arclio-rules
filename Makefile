run-dev:
	@echo "Running dev server..."
	source .env && \
	uvicorn src.main:app --port $$PORT --reload