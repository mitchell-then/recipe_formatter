.PHONY: build dev_venv

build:
	docker build -t "latex" .

dev_venv:
	python3 -m venv dev
	dev/bin/pip install -r requirements_dev.txt
