PYTHON ?= python3

.PHONY: verify
verify:
	$(PYTHON) -B -m unittest discover -s tests -v

SIBLINGS ?= ..

.PHONY: verify-integration
verify-integration:
	$(PYTHON) -B integration.py $(SIBLINGS)
