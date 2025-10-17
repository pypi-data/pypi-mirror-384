# Notes for development

Collection of random notes useful during development.

## Style

See CONTRIBUTING.md in the repository

## Releases

See RELEASING.md in the repository

## Creating new migrations
- `alembic revision -m "your_migration_name"`

## Running migrations
- `alembic upgrade head` or run the app

## Adding resources

Use the `pyside6-rcc` tool (should be available in `.venv\Scripts\`) to update QRC resources file, for example:

```Powershell
pyside6-rcc resources/icons.qrc -o iocbio/gel/gui/resources/rc_icons.py
```

## Tests
- `pip install pytest`
- `pytest .\test`
