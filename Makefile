## -*- mode: make -*-

# project specific
PROJECT            := ofxstatement-dutch
ABOUT_PY 	         := __about__.py
BRANCH 	           := master

GIT                := git

ifdef VENV_DIR
python_bin_dir := $(VENV_DIR)/bin/
else
python_bin_dir :=
endif

PYTHON             := $(python_bin_dir)python
# PYTHON is determined later on so do not use PIP := but PIP =
PIP                 = $(PYTHON) -O -m pip $(VERBOSE)
MYPY               := $(python_bin_dir)mypy
# Otherwise perl may complain on a Mac
LANG = C
PYTEST_LOG_LEVEL   := INFO
PYTEST_OPTIONS     := --log-level=$(PYTEST_LOG_LEVEL) --exitfirst

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
	PYTHONPATH=src $(PYTHON) -m pytest $(PYTEST_OPTIONS) tests

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
