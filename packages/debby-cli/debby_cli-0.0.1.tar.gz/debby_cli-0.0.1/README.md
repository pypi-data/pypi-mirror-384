# debby-core

Private projects for the getdebby.com dbt project linter.

## Setup

Install all groups with poetry.

```
poetry install --all-groups
```

### Testing

```
poetry run pytest
```

### Running the cli

```
poetry run debby
```

### Running the docs site

```
cd docs
poetry run mkdocs serve
```

### Running the web app

Make sure to install Postgres and create a database.

```
brew install postgresql
createdb debby
```

Then run the migrations and start the app

```
cd web
poetry run python manage.py migrate
poetry run python manage.py runserver
```
