export PYTHONDONTWRITEBYTECODE=1
PYTHON ?= python3

.PHONY: all run test self-test compile clean install deps

all: install

install:
	./install.sh

deps:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) run

test:
	$(PYTHON) -m unittest discover -s kapture/tests -p "test_*.py" -v

self-test:
	$(PYTHON) run --self-test

compile:
	$(PYTHON) -m compileall -q .

clean:
	rm -rf state/ captures/ build/ dist/ *.egg-info .pytest_cache 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
