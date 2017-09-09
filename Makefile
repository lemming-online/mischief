VENV=venv
BIN=$(VENV)/bin
PYTHON=$(BIN)/python
PIP=$(BIN)/pip-faster

all: build

clean-pyc:
	find . -name '*.pyc' -exec rm -rf {} +
	find . -name '*.pyo' -exec rm -rf {} +
	find . -name '*~' -exec rm -rf  {} +
	rm -rf __pycache__

clean-venv:
	rm -rf $(VENV)

clean: clean-pyc clean-venv

venv: requirements.txt requirements-dev.txt
	./venv-update venv= -ppython3 venv install= -rrequirements.txt -rrequirements-dev.txt

build: venv

run: build
	$(PYTHON) run.py
