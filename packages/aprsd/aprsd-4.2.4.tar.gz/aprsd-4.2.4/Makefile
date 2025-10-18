WORKDIR?=.
VENVDIR ?= $(WORKDIR)/.venv

.DEFAULT_GOAL := help

.PHONY: dev docs server test

include Makefile.venv
Makefile.venv:
	curl \
		-o Makefile.fetched \
		-L "https://raw.githubusercontent.com/sio/Makefile.venv/master/Makefile.venv"
	echo " fb48375ed1fd19e41e0cdcf51a4a0c6d1010dfe03b672ffc4c26a91878544f82 *Makefile.fetched" \
		| sha256sum --check - \
		&& mv Makefile.fetched Makefile.venv

help:	# Help for the Makefile
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev: REQUIREMENTS_TXT = requirements.txt requirements-dev.txt
dev: venv  ## Create a python virtual environment for development of aprsd

run: venv  ## Create a virtual environment for running aprsd commands

changelog: dev
	npm i -g auto-changelog
	auto-changelog -l false --sort-commits date -o ChangeLog.md

docs: changelog
	m2r --overwrite ChangeLog.md
	cp README.rst docs/readme.rst
	mv ChangeLog.rst docs/changelog.rst
	tox -edocs

clean: clean-dev clean-test clean-build clean-pyc ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -fr {} +
	find . -name '*.pyo' -exec rm -fr {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

clean-dev:
	rm -rf $(VENVDIR)
	rm Makefile.venv

test: dev  ## Run all the tox tests
	tox -p all

build: test changelog  ## Make the build artifact prior to doing an upload
	$(VENV)/pip install twine
	$(VENV)/python3 -m build
	$(VENV)/twine check dist/*

upload: build  ## Upload a new version of the plugin
	$(VENV)/twine upload dist/*

check: dev ## Code format check with tox and pep8
	tox -efmt-check
	tox -epep8

fix: dev ## fixes code formatting with gray
	tox -efmt

server: venv  ## Create the virtual environment and run aprsd server --loglevel DEBUG
	$(VENV)/aprsd server --loglevel DEBUG

docker: test  ## Make a docker container tagged with hemna6969/aprsd:latest
	docker build -t hemna6969/aprsd:latest -f docker/Dockerfile docker

docker-dev: test  ## Make a development docker container tagged with hemna6969/aprsd:master
	docker build -t hemna6969/aprsd:master -f docker/Dockerfile-dev docker

update-requirements: dev  ## Update the requirements.txt and dev-requirements.txt files
	rm requirements.txt
	rm requirements-dev.txt
	touch requirements.txt
	touch requirements-dev.txt
	$(VENV)/pip-compile --resolver backtracking --annotation-style=line requirements.in
	$(VENV)/pip-compile --resolver backtracking --annotation-style=line requirements-dev.in
