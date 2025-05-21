# colors
#

run-dev:
# 	@echo "Running dev server..."
# 	@docker-compose -f docker-compose.dev.yml up --build
# 	@echo "Dev server is running."
# 	@echo "To stop the server, press Ctrl+C."

run-dev:
	@echo "Running dev server..."
	source .env && \
	python main.py
	

install:
	@echo "Installing dependencies..."
	@docker-compose -f docker-compose.dev.yml run --rm app pip install -r requirements.txt
	@echo "Dependencies installed."
	@echo "To run the server, use 'make run-dev'."