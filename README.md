# PyPi cache

[![CI](https://github.com/AMDmi3/pypicache/actions/workflows/ci.yml/badge.svg)](https://github.com/AMDmi3/pypicache/actions/workflows/ci.yml)

Shamefully, [PyPi](https://pypi.org) does not provide usable
dump of metadata for all available packages.

This simple tool constantly polls
[Last Updates Feed](https://warehouse.readthedocs.io/api-reference/feeds.html#latest-updates-feed) 
for package updates, fetches recent metadata of updated packages via PyPi
[API](https://warehouse.readthedocs.io/api-reference/json.html#project),
stores it in the database and periodically generates JSON dumps.

## Running

Preparing the database:
```shell
psql --username postgres -c "CREATE DATABASE pypicache"
psql --username postgres -c "CREATE USER pypicache WITH PASSWORD 'pypicache'"
psql --username postgres -c "GRANT ALL ON DATABASE pypicache TO pypicache"
```

Running the tool:
```shell
env PYTHONPATH=. python -m pypicache --dump-path=dump.json
```
or
```shell
python setup.py install
pypicache --dump-path=dump.json
```

## Author

* [Dmitry Marakasov](https://github.com/AMDmi3) <amdmi3@amdmi3.ru>

## License

GPLv3 or later, see [COPYING](COPYING).
