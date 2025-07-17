# Documentation Generation Process (English Version)

<!-- [中文版](README_zh) -->

This document explains the workflow and tools for generating API documentation.

## Overview

The documentation system uses:

- Sphinx for API documentation generation
- Markdown for manual documentation
- Automated scripts to maintain consistency

## Key Files

### `regenerate_api_template.sh`

The main script that:

1. Automatically generates API documentation using `sphinx-apidoc`
2. Handles file exclusions via `.docignore`
3. Maintains the module index

Usage:

```bash
./regenerate_api_template.sh # directly run the script
```

or via Makefile (recommended)

```bash
make regenerate
```

### `.docignore`

Specifies files/directories to exclude from documentation generation.  
Format follows `.gitignore` conventions.

Example:

```plaintext
tests/
examples/
*_test.py
```

### `Makefile`

Contains commands for:

- Building HTML docs (`make html`)
- Cleaning generated files (`make clean`)

## Workflow

1. **Setup** (Local Development):

   Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. **Generate API Docs**:

   Run the script to generate/update API documentation:

   ```bash
   make regenerate # or ./regenerate_api_template.sh directly
   ```

3. **Build and Preview (Local Development)**:

   Build the documentation for local preview:

   ```bash
   make livehtml  # For live preview
   ```

   Then open the prompted URL in a web browser, if not automatically opened.

4. **Push Changes (Upstream Deployment)**:

   Push local changes (e.g., code updates, doc edits) to the upstream Git repository. When changes are pushed, the ReadTheDocs webhook will automatically trigger a build to update the hosted documentation.

5. **Hosted Documentation**:

   After the push, the updated documentation can be accessed via the ReadTheDocs project URL.

## Manual Documentation

Manual documentation should be written in Markdown (.md) files in:

- `source/` - Main documentation sections
- `source/api/` - API overview and usage examples (usually auto-generated)

## Maintenance

- Run `make regenerate` after significant code changes.
- Update `.docignore` when adding new test files or examples.
- For local changes, rebuild documentation (`make html` or `make livehtml`) to preview.
- On pushing to the Git repository, ensure the ReadTheDocs configuration is correct for automated builds.

## Troubleshooting

Common issues:

- **Missing modules**: Check the `MODULES` variable in `regenerate_api_template.sh`.
- **Incorrect exclusions**: Verify `.docignore` patterns.
- **Build failures during local preview**: Check Python/Sphinx versions match specified in `requirements.txt`.
- **Build failures on ReadTheDocs**: Ensure `requirements.txt` is kept up-to-date and valid for the ReadTheDocs environment.
