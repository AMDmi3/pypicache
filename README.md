# PyPi cache

[![Build Status](https://travis-ci.org/repology/pypicache.svg?branch=master)](https://travis-ci.org/repology/pypicache)

Shamefully, [PyPi](https://pypi.org) does not provide usable
dump of metadata for all available packages.

This simple tool constantly polls
[Last Updates Feed](https://warehouse.readthedocs.io/api-reference/feeds.html#latest-updates-feed) 
for package updates, fetches recent metadata of updated packages via PyPi
[API](https://warehouse.readthedocs.io/api-reference/json.html#project),
stores it in the database and periodically generates JSON dumps.

## Running

Preparing the database:
```
psql --username postgres -c "CREATE DATABASE pypicache"
psql --username postgres -c "CREATE USER pypicache WITH PASSWORD 'pypicache'"
psql --username postgres -c "GRANT ALL ON DATABASE pypicache TO pypicache"
```

Running the tool:
```
env PYTHONPATH=. python -m pypicache.py --dump-path=dump.json
```

## Author

* [Dmitry Marakasov](https://github.com/AMDmi3) <amdmi3@amdmi3.ru>

## License

GPLv3 or later, see [COPYING](COPYING).
