## -*- mode: make -*-

# project specific
PROJECT            := ofxstatement-dutch
ABOUT_PY 	         := __about__.py
BRANCH 	           := master

GIT                := git
# least important first (can not stop easily in foreach)
PYTHON_EXECUTABLES := python python3 
MYPY = mypy
# PYTHON is determined later on so do not use PIP := but PIP =
PIP                 = $(PYTHON) -O -m pip $(VERBOSE)
MYPY               := mypy
# Otherwise perl may complain on a Mac
LANG = C
PYTEST_OPTIONS     := --exitfirst

# This is GNU specific I guess
VERSION = $(shell $(PYTHON) $(ABOUT_PY))
TAG = v$(VERSION)

# OS specific section
ifeq '$(findstring ;,$(PATH))' ';'
detected_OS := Windows
HOME = $(USERPROFILE)
DEVNUL := NUL
WHICH := where
GREP := find
EXE := .exe
else
detected_OS := $(shell uname 2>/dev/null || echo Unknown)
detected_OS := $(patsubst CYGWIN%,Cygwin,$(detected_OS))
detected_OS := $(patsubst MSYS%,MSYS,$(detected_OS))
detected_OS := $(patsubst MINGW%,MSYS,$(detected_OS))
DEVNUL := /dev/null
WHICH := which
GREP := grep
EXE := 
endif

ifdef CONDA_PREFIX
home = $(subst \,/,$(CONDA_PREFIX))
else
home = $(HOME)
endif

ifdef CONDA_PYTHON_EXE
# look no further
PYTHON := $(subst \,/,$(CONDA_PYTHON_EXE))
else
# On Windows those executables may exist but not functional yet (can be used to install) so use Python -V
$(foreach e,$(PYTHON_EXECUTABLES),$(if $(shell ${e}${EXE} -V 3>${DEVNUL}),$(eval PYTHON := ${e}${EXE}),))
endif

ifndef PYTHON
$(error Could not find any Python executable from ${PYTHON_EXECUTABLES}.)
endif

.PHONY: clean install test dist upload_test upload tag

help: ## This help.
	@perl -ne 'printf(qq(%-30s  %s\n), $$1, $$2) if (m/^((?:\w|[.%-])+):.*##\s*(.*)$$/)' $(MAKEFILE_LIST)

clean: ## Cleanup the package and remove it from the Python installation path.
	$(PYTHON) setup.py clean --all
	$(GIT) clean -d -x -i

install: clean ## Install the package to the Python installation path.
	$(PIP) install -e .

test: ## Test the package.
	$(PIP) install -r test_requirements.txt
	$(MYPY) --show-error-codes src
	$(PYTHON) -m pytest --exitfirst

dist: install test ## Prepare the distribution the package by installing and testing it.
	$(PYTHON) setup.py sdist bdist_wheel
	$(PYTHON) -m twine check dist/*

upload_test: dist ## Upload the package to PyPI test.
	$(PYTHON) -m twine upload -r pypitest dist/*

upload: dist ## Upload the package to PyPI.
	$(PYTHON) -m twine upload -r pypi dist/*

tag: ## Tag the package on GitHub.
	$(GIT) tag -a $(TAG) -m "$(TAG)"
	$(GIT) push origin $(TAG)
	gh release create $(TAG) --target $(BRANCH) --title "Release $(TAG)" --notes "See CHANGELOG"
