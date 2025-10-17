# Ngawari Documentation

This directory contains the documentation for the Ngawari project, built using Sphinx.

## Building Documentation Locally

### Prerequisites

Install the documentation dependencies:

```bash
pip install -e .[docs]
```

### Build Commands

From the `docs` directory:

```bash
# Build HTML documentation
make html

# Clean build directory
make clean

# Build and serve locally
make build-and-serve
```

The built documentation will be available in `_build/html/`.

## Documentation Structure

- `index.rst` - Main documentation page
- `installation.rst` - Installation guide
- `quickstart.rst` - Quick start guide
- `api/` - API reference documentation
- `examples/` - Code examples
- `contributing.rst` - Contributing guidelines

## Configuration

The documentation is configured in `conf.py` with the following features:

- Sphinx autodoc for automatic API documentation
- Read the Docs theme
- Napoleon extension for Google/NumPy docstring support
- Intersphinx for external documentation links

## GitHub Pages Deployment

The documentation is automatically deployed to GitHub Pages via GitHub Actions when changes are pushed to the `main` or `doc` branches.

The workflow is defined in `.github/workflows/docs.yml`.

## Customization

To customize the documentation:

1. Edit the RST files in this directory
2. Modify `conf.py` for Sphinx configuration
3. Update the theme options in `conf.py` for visual customization

## Troubleshooting

If you encounter build errors:

1. Ensure all dependencies are installed: `pip install -e .[docs]`
2. Check that the Python path includes the parent directory
3. Verify that all referenced functions exist in the source code
4. Check for syntax errors in RST files 