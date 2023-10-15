## -*- mode: make -*-

# project specific
PROJECT  := ofxstatement-dutch
ABOUT_PY := __about__.py
BRANCH 	 := master

GIT = git
# least important first (can not stop easily in foreach)
PYTHON_EXECUTABLES = python python3 
MYPY = mypy
PIP = $(PYTHON) -m pip
# Otherwise perl may complain on a Mac
LANG = C
# This is GNU specific I guess
VERSION = $(shell $(PYTHON) $(ABOUT_PY))
TAG = v$(VERSION)

# OS specific section
ifeq '$(findstring ;,$(PATH))' ';'
    detected_OS := Windows
    HOME = $(USERPROFILE)
	  DEVNUL := NUL
	  WHICH := where
else
    detected_OS := $(shell uname 2>/dev/null || echo Unknown)
    detected_OS := $(patsubst CYGWIN%,Cygwin,$(detected_OS))
    detected_OS := $(patsubst MSYS%,MSYS,$(detected_OS))
    detected_OS := $(patsubst MINGW%,MSYS,$(detected_OS))
	  DEVNUL := /dev/null
	  WHICH := which
endif

$(foreach e,$(PYTHON_EXECUTABLES),$(if $(shell ${WHICH} ${e} 2>${DEVNUL}),$(eval PYTHON := ${e}),))

ifndef PYTHON
    $(error Could not find any Python executable from ${PYTHON_EXECUTABLES})
endif

ifdef CONDA_PREFIX
    home = $(CONDA_PREFIX)
else
    home = $(HOME)
endif

ifeq ($(detected_OS),Windows)
    RM_EGGS = pushd $(home) && del /s/q $(PROJECT).egg-link $(PROJECT)-nspkg.pth
else
    RM_EGGS = { cd $(home) && find . \( -name $(PROJECT).egg-link -o -name $(PROJECT)-nspkg.pth \) -print -exec rm -i "{}" \; ; }
endif

.PHONY: clean install test dist distclean upload_test upload tag

help: ## This help.
	@perl -ne 'printf(qq(%-30s  %s\n), $$1, $$2) if (m/^((?:\w|[.%-])+):.*##\s*(.*)$$/)' $(MAKEFILE_LIST)

clean: ## Cleanup the package and remove it from the Python installation path.
	$(PYTHON) setup.py clean --all
	-$(RM_EGGS)
	$(PYTHON) -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.py[co]')]"
	$(PYTHON) -Bc "import pathlib; [p.rmdir() for p in pathlib.Path('.').rglob('__pycache__')]"
	$(PYTHON) -Bc "import shutil; import os; [shutil.rmtree(d) for d in ['.pytest_cache', '.mypy_cache', 'dist', 'htmlcov', '.coverage'] if os.path.isdir(d)]"

install: clean ## Install the package to the Python installation path.
	$(PIP) install -e .

test: ## Test the package.
	$(PIP) install -r test_requirements.txt
	$(MYPY) --show-error-codes src
	$(PYTHON) -m pytest --exitfirst

dist: install ## Prepare the distribution the package by installing and testing it.
	$(PYTHON) setup.py sdist bdist_wheel
	$(PYTHON) -m twine check dist/*

distclean: ## Runs clean first and then cleans up dependency include files. 
	cd src && $(MAKE) distclean

upload_test: dist ## Upload the package to PyPI test.
	$(PYTHON) -m twine upload -r pypitest dist/*

upload: dist ## Upload the package to PyPI.
	$(PYTHON) -m twine upload -r pypi dist/*

tag: ## Tag the package on GitHub.
	$(GIT) tag -a $(TAG) -m "$(TAG)"
	$(GIT) push origin $(TAG)
	gh release create $(TAG) --target $(BRANCH) --title "Release $(TAG)" --notes "See CHANGELOG"
