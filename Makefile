VENV=venv
BIN=$(VENV)/bin
PYTHON=$(BIN)/python
PIPENV=pipenv

all: build

clean-pyc:
	find . -name '*.pyc' -exec rm -rf {} +
	find . -name '*.pyo' -exec rm -rf {} +
	find . -name '*~' -exec rm -rf  {} +
	rm -rf __pycache__

clean: clean-pyc
	$(PIPENV) uninstall --all

build: Pipfile.lock
	$(PIPENV) install --dev
	$(PIPENV) update --dev

run: build
	$(PYTHON) run.py
