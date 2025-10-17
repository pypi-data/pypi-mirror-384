# Contributing guide

## Make Changes

### Coding conventions

This project follows [PEP 8 Style Guide](https://peps.python.org/pep-0008/) in conjunction
with [The Black code style](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html#code-style).

In addition, the class attribute order should follow the list described in [setup.cfg](./setup.cfg).

### Before you commit

To reduce build pipeline usage, please check your style before pushing your code.
```bash
python -m pip install flake8
python -m pip install flake8-class-attributes-order
python -m pip install black
```

Run both the [Black formatter](https://black.readthedocs.io/en/stable/index.html) and
[Flake8 style checker](https://flake8.pycqa.org/en/latest/) via console `black iocbio` and `flake8`
or through your IDE and fix any issues they rise.

## Changes in database schema

Changes in database schema are handled through
[alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html). 

For introduce changes in the database, go to database schema definition by
alembic and check if history is recognized (assuming that `alembic` command is
in your path):
```
cd iocbio/gel/db/alembic
alembic history
```

To add new revision, run:
```
alembic revision -m "revision name"
```
and adjust created Python script under `iocbio/gel/db/alembic/versions`. Note
that you can use `execute_sqlite.py` module for running SQL scripts directly.
See other revision scripts for examples.

In general, we support only updates of the schema and `downgrade` function can
be kept empty.

See also earlier migrations for examples on how to do it with SQLite.