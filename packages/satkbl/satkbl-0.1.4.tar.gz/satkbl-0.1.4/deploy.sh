uv run hatch clean
uv run pyproject-build
#uv run twine upload --repository testpypi dist/*

uv run twine upload dist/* 