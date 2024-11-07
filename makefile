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

clean:
	@find . -type d -name "__pycache__" -exec rm -r {} +
	@find . -type d -name ".mypy_cache" -exec rm -r {} +
	@find . -type d -name ".pytest_cache" -exec rm -r {} +
	@find . -type d -name "htmlcov" -exec rm -r {} +
	@find . -type f -name ".coverage" -exec rm -r {} +
