ifeq ($(OS),Windows_NT)
PYTHON = .venv/Scripts/python.exe
else
PYTHON = .venv/bin/python
endif

.PHONY: setup data features train inventory simulate api dashboard test
setup:
	python -m venv .venv
	$(PYTHON) -m pip install -r requirements.txt
data:
	$(PYTHON) -m src.cli data
features:
	$(PYTHON) -m src.cli features
train:
	$(PYTHON) -m src.cli train
inventory:
	$(PYTHON) -m src.cli inventory
simulate:
	$(PYTHON) -m src.cli simulate
api:
	$(PYTHON) -m src.cli api
dashboard:
	$(PYTHON) -m src.cli dashboard
test:
	$(PYTHON) -m pytest -q
