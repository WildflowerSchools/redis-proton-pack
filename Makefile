.PHONY: lint test

test:
	pytest --cov-report term-missing --cov=protonpack -v tests/

lint:
	pip install pycodestyle
	python -m pycodestyle . --ignore E501,E252
