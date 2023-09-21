# analyze-stocks

##### Usage
```sh
hypercorn app.main:app --reload -b 127.0.0.1:3000
```

##### Initial Setup
```sh
alembic init alembic
```
update alembic.ini db creds and env.py metadata

##### Create Migrations/revision
```sh
alembic revision --autogenerate -m "init revision"
```

##### Migrate
```sh
alembic upgrade head
```