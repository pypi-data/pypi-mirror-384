# alxhttp
Some customization of aiohttp

Features:
- JSON logging
- middleware to add a unique request ID
- middleware to turn uncaught exceptions into JSON 500s
- a simple base server class pattern to follow

# Publish
uv run pyright --createstub alxhttp
rsync -a typings/alxhttp/ alxhttp/
rm -rf typings
uv build
find alxhttp |  grep pyi | xargs rm
twine upload dist/*
