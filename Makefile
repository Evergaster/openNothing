UV := $(shell command -v uv 2>/dev/null || echo uv)
VENV ?= .venv
ARGS ?=

.PHONY: install install-dev run test uninstall clean

# instala opennothing como aplicacion global en el sistema (~/.local/bin)
# deja disponible el comando: opennothing
install:
	$(UV) tool install --force .

# venv de desarrollo + instalacion editable
install-dev:
	$(UV) venv $(VENV)
	$(UV) pip install -e .

# ejecuta el CLI (usa el venv de desarrollo si existe)
run:
	$(UV) run python -m opennothing $(ARGS)

test:
	$(UV) run python -m unittest discover -s tests -v

uninstall:
	$(UV) tool uninstall opennothing

clean:
	rm -rf $(VENV) .pytest_cache __pycache__ */__pycache__