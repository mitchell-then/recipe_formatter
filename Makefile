# Author: Mitchell Then

.PHONY: build run dev_venv

build:
	docker build -t "latex" .

run:
	docker run --rm -v $(RPATH):/data latex /root/make_pdfs.py /data/Recipes_src/ /data/Recipes/

dev_venv:
	python3 -m venv dev
	dev/bin/pip install -r requirements_dev.txt
