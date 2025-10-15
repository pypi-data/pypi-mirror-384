## Step 3: Build the Package

```bash
# Install build tools
pip install build twine

# Clean old builds
rm -rf dist/ build/ *.egg-info src/xatra.egg-info

# Build the package (this will NOT include data/ directory)
python -m build
```

This creates:
- `dist/xatra-2.0.0-py3-none-any.whl` (wheel)
- `dist/xatra-2.0.0.tar.gz` (source distribution)

The package will be small (~100KB) since data is not included.

## Step 4: Test Installation Locally

```bash
# Create a test environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install the built package
pip install dist/xatra-2.0.0-py3-none-any.whl

# Test data installation
xatra-install-data

# Test import and usage
python -c "import xatra; print('Xatra version:', xatra.__version__)"
```

## Step 5: Upload to PyPI

### Test PyPI (Recommended First)

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ xatra
```

### Production PyPI

```bash
# Upload to PyPI
twine upload dist/*
```

## User Installation Flow

After publishing, users will install with:

```bash
# 1. Install the package
pip install xatra

# 2. Install data (separate step)
xatra-install-data
```

The data installer will:
1. Create `~/.xatra/data/`
2. Download data from Hugging Face (~500MB-1GB)
3. Verify data integrity

## Package Structure

After installation, users will have:

```
~/.xatra/data/
├── disputed_territories/
│   ├── disputed_gid_list.json
│   ├── disputed_mapping.json
│   └── ...
├── gadm/
│   ├── gadm41_AFG_0.json
│   ├── gadm41_AFG_1.json
│   └── ... (all country files)
├── ne_10m_rivers.geojson
└── rivers_overpass_india/
    └── ... (river files)
```

## Troubleshooting

### Data Not Found Error

If users see a warning about missing data:
```
UserWarning: XATRA DATA NOT FOUND
```

They should run:
```bash
xatra-install-data
```

### Force Re-download

If data becomes corrupted:
```bash
xatra-install-data --force
```

### Check Installation

To verify data is installed:
```bash
xatra-install-data --check
```

### Manual Installation

If automatic download fails, users can manually download:
1. Visit: https://huggingface.co/datasets/your-username/xatra-data
2. Download the data directory
3. Extract to: `~/.xatra/data/`

## Version Updates

When updating the package:

1. Update version in `pyproject.toml`
2. Rebuild: `python -m build`
3. Upload: `twine upload dist/*`

When updating data:

1. Upload new data to Hugging Face (overwrites old data)
2. Users run: `xatra-install-data --force` to update
