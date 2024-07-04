# analyze-stocks

##### Installation
```sh
poetry shell
poetry install 
```
update alembic.ini db creds and env.py metadata

##### Usage
```sh
hypercorn app.main:app --reload -b 127.0.0.1:3000
```

##### Create Migrations/revision
```sh
alembic revision --autogenerate -m "<Name of the migration>"
```

##### Migrate
```sh
alembic upgrade head
```
