# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

VENV ?= venv
PYTHON ?= $(VENV)/bin/python3
PIP ?= $(PYTHON) -m pip

BASE_DIR = $(shell pwd)
PYTHONPATH = $(BASE_DIR)
OPENAPI_DIR = $(BASE_DIR)/openapi
OPENAPI_JSON = $(OPENAPI_DIR)/dyff.json
OPENAPI_CLIENT_DIR = $(BASE_DIR)/dyff/client
OPENAPI_NAMESPACE = _generated
OPENAPI_GENERATED_DIR = $(OPENAPI_CLIENT_DIR)/$(OPENAPI_NAMESPACE)

.PHONY: all
all: $(VENV)

$(VENV):
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip setuptools wheel pip-tools

.PHONY: openapi
openapi: $(OPENAPI_GENERATED_DIR)

$(OPENAPI_GENERATED_DIR): $(OPENAPI_JSON)
	npx autorest --v3 --input-file=$(OPENAPI_JSON) --python --python3-only --output-folder=$(OPENAPI_CLIENT_DIR) --namespace=$(OPENAPI_NAMESPACE)
	isort $(OPENAPI_GENERATED_DIR)
	black $(OPENAPI_GENERATED_DIR)

.PHONY: clean
clean:
	rm -f $(OPENAPI_JSON)
	rm -rf $(OPENAPI_DIR)

.PHONY: distclean
distclean:
	rm -rf node_modules/ $(VENV)
	find -name __pycache__ -type d -exec rm -rf '{}' \;
	find -name \*.pyc -type f -exec rm -f '{}' \;
