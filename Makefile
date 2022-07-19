## -*- mode: make -*-

GIT = git
PYTHON = python
MYPY = mypy
PIP = pip
PROJECT = ofxstatement-dutch
# Otherwise perl may complain on a Mac
LANG = C

# OS specific section
ifeq '$(findstring ;,$(PATH))' ';'
    detected_OS := Windows
else
    detected_OS := $(shell uname 2>/dev/null || echo Unknown)
    detected_OS := $(patsubst CYGWIN%,Cygwin,$(detected_OS))
    detected_OS := $(patsubst MSYS%,MSYS,$(detected_OS))
    detected_OS := $(patsubst MINGW%,MSYS,$(detected_OS))
endif

ifeq ($(detected_OS),Windows)
    RM_EGGS = pushd $(CONDA_PREFIX) && del /s/p $(PROJECT).egg-link $(PROJECT)-nspkg.pth
else
    RM_EGGS = cd $(CONDA_PREFIX) && find . \( -name $(PROJECT).egg-link -o -name $(PROJECT)-nspkg.pth \) -exec rm -i {} \;
endif

.PHONY: clean install test dist distclean upload

help: ## This help.
	@perl -ne 'printf(qq(%-30s  %s\n), $$1, $$2) if (m/^((?:\w|[.%-])+):.*##\s*(.*)$$/)' $(MAKEFILE_LIST)

clean: ## Cleanup the package and remove it from the Python installation path.
	$(PYTHON) setup.py clean --all
	$(RM_EGGS)
	$(PYTHON) -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.py[co]')]"
	$(PYTHON) -Bc "import pathlib; [p.rmdir() for p in pathlib.Path('.').rglob('__pycache__')]"
	-$(PYTHON) -Bc "import shutil; shutil.rmtree('.pytest_cache')"

install: clean ## Install the package to the Python installation path.
	$(PIP) install -e .
	$(PIP) install -r test_requirements.txt

test: ## Test the package.
	$(MYPY) --show-error-codes src
	$(PYTHON) -m pytest --exitfirst

dist: install test ## Prepare the distribution the package by installing and testing it.
	$(PYTHON) setup.py sdist bdist_wheel
	$(PYTHON) -m twine check dist/*

upload_test: dist ## Upload the package to PyPI test.
	$(PYTHON) -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

upload: dist ## Upload the package to PyPI.
	$(PYTHON) -m twine upload dist/*

# This is GNU specific I guess
VERSION = $(shell $(PYTHON) __about__.py)

TAG = v$(VERSION)

tag: ## Tag the package on GitHub.
	git tag -a $(TAG) -m "$(TAG)"
	git push origin $(TAG)
