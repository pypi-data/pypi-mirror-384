# Publishing Arc Superset Dialect

This document describes how to publish the Arc SQLAlchemy dialect for Apache Superset.

## Option 1: Publish to PyPI (Recommended)

### Prerequisites

1. Create PyPI account at https://pypi.org/account/register/
2. Install publishing tools:
   ```bash
   pip install build twine
   ```

### Publishing Steps

1. **Update version in setup.py** (increment for each release)

2. **Build the package**:
   ```bash
   python -m build
   ```

   This creates:
   - `dist/arc-superset-dialect-1.0.0.tar.gz` (source distribution)
   - `dist/arc_superset_dialect-1.0.0-py3-none-any.whl` (wheel)

3. **Test with TestPyPI** (optional but recommended):
   ```bash
   twine upload --repository testpypi dist/*
   ```

4. **Upload to PyPI**:
   ```bash
   twine upload dist/*
   ```

5. **Verify installation**:
   ```bash
   pip install arc-superset-dialect
   ```

### Using in Superset

Users can add Arc support to their Superset installation:

```dockerfile
FROM apache/superset:latest

USER root
RUN pip install arc-superset-dialect
USER superset
```

Or in existing Superset:
```bash
docker exec -it superset_app pip install arc-superset-dialect
docker restart superset_app
```

Connection string:
```
arc://YOUR_API_KEY@arc-api:8000/default
```

## Option 2: Contribute to Apache Superset

This makes Arc a first-class supported database in Superset's UI.

### Steps

1. **Fork Superset repository**:
   ```bash
   git clone https://github.com/apache/superset.git
   cd superset
   git remote add upstream https://github.com/apache/superset.git
   ```

2. **Add Arc dialect** to `superset/db_engine_specs/`:

   Create `superset/db_engine_specs/arc.py`:
   ```python
   from superset.db_engine_specs.base import BaseEngineSpec

   class ArcEngineSpec(BaseEngineSpec):
       engine = "arc"
       engine_name = "Arc"

       # Enable time range selector in UI
       _time_grain_expressions = {
           None: "{col}",
           "PT1S": "DATE_TRUNC('second', {col})",
           "PT1M": "DATE_TRUNC('minute', {col})",
           "PT1H": "DATE_TRUNC('hour', {col})",
           "P1D": "DATE_TRUNC('day', {col})",
           "P1W": "DATE_TRUNC('week', {col})",
           "P1M": "DATE_TRUNC('month', {col})",
           "P1Y": "DATE_TRUNC('year', {col})",
       }
   ```

3. **Add dialect to requirements**:

   Edit `setup.py` to include:
   ```python
   "arc": ["arc-superset-dialect>=1.0.0"],
   ```

4. **Add Arc logo** to `superset/static/assets/images/` (optional)

5. **Run tests**:
   ```bash
   pytest tests/db_engine_specs/test_arc.py
   ```

6. **Create Pull Request**:
   - Title: "feat: Add Arc time-series database support"
   - Description: Include connection string format, use cases, and links to Arc docs
   - Reference: https://github.com/apache/superset/pulls

### PR Guidelines

- Follow [Apache Superset contribution guidelines](https://github.com/apache/superset/blob/master/CONTRIBUTING.md)
- Add tests for the engine spec
- Update documentation in `docs/docs/databases/`
- Include example dashboard screenshots
- Sign Apache CLA

## Recommended Approach

**Start with Option 1 (PyPI)** for immediate availability, then pursue Option 2 for official support.

Benefits:
- **PyPI**: Users can install today, you control releases
- **Official**: Better visibility, appears in Superset's database picker UI

## Repository Setup

Create a new repository at `https://github.com/basekick-labs/arc-superset-dialect`:

```bash
cd /Users/nacho/dev/basekick-labs
mkdir arc-superset-dialect
cd arc-superset-dialect

# Copy files
cp -r /Users/nacho/dev/exydata.ventures/historian_product/superset/* .

# Initialize git
git init
git add .
git commit -m "Initial commit: Arc SQLAlchemy dialect for Superset"
git remote add origin https://github.com/basekick-labs/arc-superset-dialect.git
git push -u origin main
```

## Versioning

Use semantic versioning:
- `1.0.0` - Initial stable release
- `1.0.1` - Bug fixes
- `1.1.0` - New features (backwards compatible)
- `2.0.0` - Breaking changes

## Release Checklist

- [ ] Update version in setup.py
- [ ] Update CHANGELOG.md
- [ ] Run tests
- [ ] Build package: `python -m build`
- [ ] Upload to PyPI: `twine upload dist/*`
- [ ] Create GitHub release tag
- [ ] Update documentation

## Support

After publishing:
- Monitor GitHub issues
- Update PyPI page with latest docs
- Announce on Discord and Arc community
