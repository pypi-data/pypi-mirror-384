# py-pve-cloud

this is the core python library package that serves as a foundation for pve cloud.

## alembic orm

this project uses sqlalchemy + alembic integrated into the collection for management of the patroni database schema.

edit `src/orm/alchemy.py` database classes and run `alembic revision --auto-enerate -m "revision description"` from the orm folder, to commit your changes into the general migrations. before you need to do a `pip install .` to get the needed orm pypi packages.

you also need to `export PG_CONN_STR=postgresql+psycopg2://postgres:{{ patroni_postgres_pw }}@{{ proxy or master ip }}:{{ 5000 / 5432 }}/pve_cloud?sslmode=disable` env variable first with a testing database for alembic to work against. to create a new migration the database needs to be on the latest version, run `alembic upgrade head` to upgrade it.


## Releasing to pypi

```bash
pip install build twine
rm -rf dist
python3 -m build
python3 -m twine upload dist/*
```
