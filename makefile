install:
	@poetry env use python3.13
	@poetry lock
	@poetry install --no-root

run_main:
	@poetry run python src/main_server.py

run_proxies:
	@poetry run python src/proxy_server.py

run_tests:
	@poetry run pytest tests/
