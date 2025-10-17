setup:
	uv venv && uv sync
	@echo "activate: source ./.venv/bin/activate"

up:
	docker compose up -d --wait

db_open:
	open -a TablePlus $$DATABASE_URL

lint:
	pyright
	ruff format

clean:
	rm -rf *.egg-info
	rm -rf .venv
