.PHONY: all data check excel images clean install

PYTHON ?= python3
VENV ?= .venv

all: install data check excel images

install:
	$(PYTHON) -m venv $(VENV) 2>/dev/null || true
	$(VENV)/bin/pip install -q -r requirements.txt

data:
	cd scripts && ../$(VENV)/bin/python generate_data.py

check:
	cd scripts && ../$(VENV)/bin/python check_reconciliation.py

excel:
	cd scripts && ../$(VENV)/bin/python build_excel.py

images:
	cd scripts && ../$(VENV)/bin/python render_dashboards.py

clean:
	rm -rf data/*.csv excel/*.xlsx images/*.png config/exchange_rate.json

run:
	$(VENV)/bin/python run_all.py
