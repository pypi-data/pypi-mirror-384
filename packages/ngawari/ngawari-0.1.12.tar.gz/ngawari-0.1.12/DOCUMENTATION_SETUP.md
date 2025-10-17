# Ngawari Documentation Setup

This document describes the complete documentation setup for the Ngawari project, including the corrections made to ensure all documented functions actually exist in the codebase.

## Overview

The documentation system has been set up with:
- **Sphinx** for documentation generation
- **Read the Docs theme** for modern styling
- **Auto-generated API docs** from docstrings
- **GitHub Pages deployment** via GitHub Actions
- **Local development tools** for testing

## Project Structure

```
ngawari/
├── docs/
│   ├── conf.py              # Sphinx configuration
│   ├── index.rst            # Main documentation page
│   ├── quickstart.rst       # Quick start guide
│   ├── installation.rst     # Installation instructions
│   ├── api/                 # API documentation
│   │   ├── index.rst        # API overview
│   │   ├── ftk.rst          # ftk module documentation
│   │   ├── fIO.rst          # fIO module documentation
│   │   └── vtkfilters.rst   # vtkfilters module documentation
│   ├── examples/            # Example code
│   │   └── index.rst        # Example documentation
│   ├── contributing.rst     # Contributing guidelines
│   ├── Makefile             # Documentation build commands
│   ├── requirements.txt     # Documentation dependencies
│   ├── build_docs.py        # Helper script for building docs
│   └── _build/              # Generated documentation (gitignored)
├── .github/workflows/
│   └── docs.yml             # GitHub Actions workflow for docs
└── pyproject.toml           # Updated with docs dependencies
```

## Key Corrections Made

### 1. Function Verification
All documented functions have been verified to actually exist in the codebase:

**ftk module real functions:**
- `normaliseArray`, `fcdot`, `angleBetween2Vec`, `distTwoPoints`
- `rotationMatrixFromThreeAngles`, `buildRotationMatrix`, `rotateArray`
- `fitPlaneToPoints`, `fitPlaneToPointCloud_RANSAC`, `buildCircle3D`
- `getIdOfPointClosestToX`, `distPointPoints`, `cumulativeDistanceAlongLine`
- `rad2deg`, `deg2rad`, `setVecAConsitentWithVecB`

**fIO module real functions:**
- `readVTKFile`, `writeVTKFile` (replaces hallucinated loadVTP/saveVTP etc.)
- `writePlyFile`, `readNifti`, `writeNifti`, `readNRRD`
- `readPVD`, `writeVTK_PVD_Dict`, `pvdGetTimes`, `pvdGetDataClosestTo`
- `pickleData`, `unpickleData`
- `getAllFilesUnderDir`, `countFilesInDir`

**vtkfilters module real functions:**
- `isVTI`, `isVTP`, `isVTS`
- `getArrayNames`, `getArray`, `getArrayAsNumpy`, `setArrayFromNumpy`
- `buildSphereSource`, `buildCylinderSource`, `buildCubeSource`
- `contourFilter`, `cleanData`, `filterBoolean`, `tubeFilter`
- `clipDataByPlane`, `getPolyDataClippedBySphere`, `clippedByScalar`
- `buildRawImageData`, `filterVtiMedian`, `filterResampleToImage`
- `filterGetPointsInsideSurface`, `filterGetEnclosedPts`
- `vtiToVts`, `vtsToVti`, `pointToCellData`, `cellToPointData`

### 2. Updated Examples
All examples now use only real functions:
- Removed references to non-existent functions like `crossProduct`, `dotProduct`
- Replaced `loadVTP/saveVTP` with `readVTKFile/writeVTKFile`
- Used correct function names and parameters
- Added proper imports and error handling

### 3. API Documentation
- Removed all hallucinated function references
- Organized functions by logical categories
- Added proper cross-references between modules
- Ensured all autofunction directives reference real functions

## Installation

### For Users
```bash
pip install ngawari[docs]
```

### For Developers
```bash
# Clone the repository
git clone <repository-url>
cd ngawari

# Install in development mode with docs
pip install -e .[docs]

# Build documentation locally
python docs/build_docs.py build
```

## Building Documentation

### Local Development
```bash
# Build documentation
python docs/build_docs.py build

# Serve documentation locally
python docs/build_docs.py serve

# Clean build directory
python docs/build_docs.py clean

# Check for issues
python docs/build_docs.py check
```

### Using Makefile
```bash
cd docs
make html      # Build HTML documentation
make clean     # Clean build directory
make serve     # Serve locally (requires sphinx-autobuild)
```

## GitHub Pages Deployment

The documentation is automatically deployed to GitHub Pages when:
- Code is pushed to the `main` branch
- Code is pushed to the `doc` branch

### Setup Instructions
1. Go to your repository settings
2. Navigate to "Pages" section
3. Set source to "GitHub Actions"
4. The workflow will automatically build and deploy

### Workflow Details
The GitHub Actions workflow (`.github/workflows/docs.yml`):
- Runs on Ubuntu latest
- Uses Python 3.9+
- Installs dependencies including VTK
- Builds documentation with Sphinx
- Deploys to GitHub Pages

## Customization

### Theme
The documentation uses the Read the Docs theme. To customize:
1. Edit `docs/conf.py`
2. Modify `html_theme_options`
3. Add custom CSS in `docs/_static/`

### Configuration
Key settings in `docs/conf.py`:
- `project` and `copyright` information
- `extensions` for autodoc, napoleon, etc.
- `html_theme` and theme options
- `autodoc_default_options` for API docs

### Adding New Pages
1. Create new `.rst` files in appropriate directories
2. Add to `toctree` in parent index files
3. Update navigation as needed

## Troubleshooting

### Common Issues

**Import Errors**
- Ensure VTK is properly installed
- Check Python path and virtual environment
- Verify all dependencies are installed

**Build Errors**
- Check for syntax errors in RST files
- Verify all referenced functions exist
- Ensure proper indentation in RST files

**Missing Functions**
- All functions are now verified to exist
- Check module imports in `ngawari/__init__.py`
- Verify function signatures match documentation

### Debugging
```bash
# Verbose build output
python docs/build_docs.py build --verbose

# Check specific modules
python -c "import ngawari.ftk; print(dir(ngawari.ftk))"
```

## Next Steps

### For Users
1. Read the :doc:`quickstart` guide
2. Explore the :doc:`api/index` for available functions
3. Check :doc:`examples/index` for practical examples

### For Contributors
1. Read :doc:`contributing` guidelines
2. Ensure all new functions are documented
3. Test documentation builds locally before submitting PRs

### For Maintainers
1. Review and update documentation with each release
2. Ensure all new features are documented
3. Keep examples up to date with API changes

## Maintenance

### Regular Tasks
- Update version numbers in documentation
- Review and update examples for new features
- Check for broken links and references
- Update installation instructions for new dependencies

### Quality Assurance
- All functions are verified to exist in codebase
- Examples are tested and functional
- Documentation builds without errors
- Cross-references are accurate and working

This documentation setup provides a solid foundation for the Ngawari project with accurate, comprehensive, and maintainable documentation that users can rely on. 