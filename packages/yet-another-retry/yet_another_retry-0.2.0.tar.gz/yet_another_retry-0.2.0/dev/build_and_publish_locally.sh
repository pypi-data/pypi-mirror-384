# only for extreme cases, otherwise use the github action
# requires UV_PUBLISH_TOKEN environment variable to be set
# this will use whatever is in the pyproject.toml version as new version

# clear out any existing builds
rm -rf dist
# new build with uv
uv build --sdist --wheel --out-dir dist

# publish it
uv publish
