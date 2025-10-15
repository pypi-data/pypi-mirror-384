# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Run sphinx-apidoc to generate API rst files before building docs.
# Set APIDOC=0 to skip this step when calling make.
APIDOC ?= 1
# Prefer the sphinx-apidoc CLI if available, otherwise run via the selected Python
PYTHON ?= python
APIDOC_CMD := $(shell if command -v sphinx-apidoc >/dev/null 2>&1; then \
        printf "sphinx-apidoc -o $(SOURCEDIR)/api ../src/xpcscorr -f"; \
    else \
        printf "$(PYTHON) -m sphinx.apidoc -o $(SOURCEDIR)/api ../src/xpcscorr -f"; \
    fi)

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Clean target to remove api and build directories
clean:
	@echo "Cleaning build and API directories..."
	@rm -rf "$(BUILDDIR)"
	@rm -rf "$(SOURCEDIR)/api"

.PHONY: help clean Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@if [ "$(APIDOC)" = "1" ]; then \
		echo "Running sphinx-apidoc..."; \
    	$(APIDOC_CMD); \
	fi
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

html: clean