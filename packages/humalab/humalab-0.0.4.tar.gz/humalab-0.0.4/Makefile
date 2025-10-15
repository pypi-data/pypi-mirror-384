.PHONY: clean build upload upload-test install dev

clean:
	rm -rf dist/ build/ *.egg-info

build: clean
	python -m build

upload: build
	twine upload dist/*

upload-test: build
	twine upload --repository testpypi dist/*

install:
	pip install -e .

dev:
	pip install -e ".[dev]"
