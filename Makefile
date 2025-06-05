# Colors
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
CYAN   := $(shell tput -Txterm setaf 6)
RESET  := $(shell tput -Txterm sgr0)


install: ## Install & sync backend dependencies
	@echo "${GREEN}Installing backend dependencies...${RESET}"
	source .env && \
	uv pip install -e .
	uv sync
	@echo "${GREEN}Backend dependencies installed.${RESET}"

# For Python Development
lint:	## Run linting tools
	uv tool run ruff check --fix .

type-check: ## Run type checking
	uv tool run pyright .

format:  ## Format code
	uv tool run ruff format .

pre-commit: ## Run pre-commit checks (combines lint, type-check and format)
	make format && \
	make lint && \
	make type-check


run-dev: ## Run the development server using stdio
	@echo "$(YELLOW)Starting development server using stdio...$(RESET)"
	source .env && \
	arclio-rules

# SOPS
init-key: ## Generate new age key and configure shell
	@mkdir -p ~/.config/sops
	@[ -f ~/.config/sops/key.txt ] && echo "${YELLOW}Key already exists at ~/.config/sops/key.txt${RESET}" || age-keygen -o ~/.config/sops/key.txt
	@echo "${GREEN}Setting up SOPS environment...${RESET}"
	@export SOPS_AGE_KEY_FILE=~/.config/sops/key.txt
	@if [ -f ~/.zshrc ] && ! grep -q "export SOPS_AGE_KEY_FILE" ~/.zshrc; then \
		echo 'export SOPS_AGE_KEY_FILE=~/.config/sops/key.txt' >> ~/.zshrc; \
		echo "${GREEN}Added to ~/.zshrc${RESET}"; \
	elif [ -f ~/.bashrc ] && ! grep -q "export SOPS_AGE_KEY_FILE" ~/.bashrc; then \
		echo 'export SOPS_AGE_KEY_FILE=~/.config/sops/key.txt' >> ~/.bashrc; \
		echo "${GREEN}Added to ~/.bashrc${RESET}"; \
	fi
	@echo "${GREEN}SOPS environment setup complete. Run '${CYAN}source ~/.zshrc${RESET}' or '${CYAN}source ~/.bashrc${RESET}' to apply changes${RESET}"
	@echo "\nYour public key (share this with your team lead):"
	@cat ~/.config/sops/key.txt | grep "public key:"

# SOPS
encrypt: ## Encrypt .env to .env.sops
	@if [ ! -f ".env" ]; then \
		echo "${YELLOW}Error: .env file not found${RESET}"; \
		exit 1; \
	fi
	@if [ -z "$$SOPS_AGE_KEY_FILE" ]; then \
		echo "${YELLOW}Error: SOPS_AGE_KEY_FILE not set. Try: source ~/.zshrc ${RESET}"; \
		exit 1; \
	fi
	@KEY_PATH=$$(eval echo $$SOPS_AGE_KEY_FILE); \
	if [ ! -f "$$KEY_PATH" ]; then \
		echo "${YELLOW}Error: Age key not found at $$KEY_PATH${RESET}"; \
		echo "${YELLOW}Try: make init-key${RESET}"; \
		exit 1; \
	fi
	@echo "${GREEN}Encrypting .env to .env.sops...${RESET}"
	@SOPS_AGE_KEY_FILE="$$KEY_PATH" sops --input-type dotenv --output-type yaml -e .env > .env.sops
	@echo "${GREEN}Encryption complete${RESET}"

decrypt: ## Decrypt .env.sops to .env
	@if [ -z "$$SOPS_AGE_KEY_FILE" ]; then \
		echo "${YELLOW}Error: SOPS_AGE_KEY_FILE not set. Try: source ~/.zshrc ${RESET}"; \
		exit 1; \
	fi
	@KEY_PATH=$$(eval echo $$SOPS_AGE_KEY_FILE); \
	echo "${CYAN}Debug: SOPS_AGE_KEY_FILE=$$SOPS_AGE_KEY_FILE${RESET}"; \
	echo "${CYAN}Debug: KEY_PATH=$$KEY_PATH${RESET}"; \
	if [ ! -f "$$KEY_PATH" ]; then \
		echo "${YELLOW}Error: Age key not found at $$KEY_PATH${RESET}"; \
		echo "${YELLOW}Try: make init-key${RESET}"; \
		exit 1; \
	fi
	@echo "${GREEN}Decrypting .env.sops to .env...${RESET}"
	@echo "${CYAN}Debug: Running command with key file: $$KEY_PATH${RESET}"
	@if [ "$$(uname)" = "Darwin" ]; then \
		SOPS_AGE_KEY_FILE=/Users/$$USER/.config/sops/key.txt sops --input-type yaml --output-type dotenv -d .env.sops > .env 2>/tmp/sops_error; \
	else \
		SOPS_AGE_KEY_FILE=/home/$$USER/.config/sops/key.txt sops --input-type yaml --output-type dotenv -d .env.sops > .env 2>/tmp/sops_error; \
	fi || { \
		echo "${YELLOW}Decryption failed. You might need to:${RESET}"; \
		echo "1. Check if your key is in .sops.yaml: ${CYAN}cat .sops.yaml${RESET}"; \
		echo "2. Re-encrypt with your key: ${CYAN}make encrypt${RESET}"; \
		echo "3. Or get fresh secrets and re-encrypt"; \
		echo "\nFull error:"; \
		cat /tmp/sops_error; \
		exit 1; \
	}
	@echo "${GREEN}Decryption complete${RESET}"

add-recipient: ## Add new public key (make add-recipient KEY=age1...)
	@if [ -z "$(KEY)" ]; then \
		echo "${YELLOW}Usage: make add-recipient KEY=age1...${RESET}"; \
		exit 1; \
	fi
	@if grep -q "$(KEY)" .sops.yaml; then \
		echo "${YELLOW}Key already exists in .sops.yaml${RESET}"; \
	else \
		awk '/^    age:/{print;print "     $(KEY),";next}1' .sops.yaml > .sops.yaml.tmp && \
		mv .sops.yaml.tmp .sops.yaml && \
		echo "${GREEN}Added key to .sops.yaml${RESET}"; \
	fi

build: ## Build the backend
	source .env && \
	uv build

publish: ## Publish the package to PyPI
	@echo "${YELLOW}Uploading to PyPI...${RESET}"
	python -m twine upload --repository pypi dist/* --verbose
	@echo "${GREEN}Package uploaded successfully.${RESET}"