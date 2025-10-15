SHELL=/bin/bash
DIRNAME := $(shell basename $$(pwd))
SITEPKGS := $(shell python3 -c 'import site; print(site.getsitepackages()[0])')

help:
	@echo
	@echo "Synopsis: make [ build clean vars version ]"
	@echo

vars:
	@echo "DIRNAME: '${DIRNAME}'"
	@echo "SITEPKGS: '${SITEPKGS}'"

version: pkg_deps
	python3 -m setuptools_scm

build: pkg_deps
	python3 -m build

pkg_deps: ${SITEPKGS}/build ${SITEPKGS}/setuptools_scm

${SITEPKGS}/build:
	python3 -m pip install --upgrade build

${SITEPKGS}/setuptools_scm:
	python3 -m pip install --upgrade setuptools-scm

clean:
	rm -rf dist/
	rm -rf ipf.egg-info/
