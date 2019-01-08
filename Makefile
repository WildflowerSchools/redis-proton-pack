.PHONY: lint test

test:
	SPY_LOG_LOGGER=json-clean SPY_LOG_LEVEL=DEBUG SPY_SHOW_META=False pytest --cov-report term-missing --cov=protonpack -v tests/

lint:
	pip install pycodestyle
	python -m pycodestyle . --ignore E501,E252
