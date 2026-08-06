---
name: KHAP Python package install
description: How to install Python packages in this Replit Nix environment — pip and uv --system both fail.
---

## Rule

Install Python packages with:

```bash
uv pip install --target /home/runner/workspace/.pythonlibs/lib/python3.13/site-packages <packages>
```

**Why:** The default `python` is Python 3.13 (Nix-managed, immutable). The `.pythonlibs` directory is the writable Replit-managed site-packages. `pip`, `uv --system`, and `uv --python .pythonlibs/bin/python3.12` all fail because they resolve to the immutable Nix store.

**How to apply:** Any time new Python dependencies are needed for this project, use the exact command above. The packages installed in python3.12 site-packages are NOT picked up by the running python3.13 process.

## Verify

```bash
python -c "import fastapi, sqlalchemy, geoalchemy2, pydantic_settings; print('ok')"
```
