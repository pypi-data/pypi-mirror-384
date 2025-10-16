# Instructions for development

This package was built with the intention of it being built and tested with astral uv.  
The only dependency for development is pytest  

You can then run pytest with
```bash
uv run pytest
```
this will automatically install dev dependencies to the .venv  

To remove all dev dependencies from the virtual environment
```bash
uv sync --no-group dev
```
