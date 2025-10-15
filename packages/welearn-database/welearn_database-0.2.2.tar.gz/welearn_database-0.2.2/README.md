# WeLearn Database

This repository contains the database schema and sample data for the WeLearn application, an online learning platform.

## Pypi Package
You can install this pacakge via pypi :

```bash
pip install welearn-database
```
or you can read pypi page [here](https://pypi.org/project/welearn-database/)

## Environment Variables
Before running the application, make sure to set the following environment variables:
```
PG_USER=<pg user>
PG_PASSWORD=<pg password>
PG_HOST=<pg address>
PG_PORT=<pg port, 5432 by default>
PG_DB=<pg database name>
PG_DRIVER=<driver to use, pg default is : postgresql+psycopg2>
PG_SCHEMA=document_related,corpus_related,user_related,agent_related
LOG_LEVEL=INFO
LOG_FORMAT=[%(asctime)s][%(name)s][%(levelname)s] - %(message)s
```

## Database Schema
The database schema is organized into four main schemas:
- `document_related`: Contains tables related to documents and their metadata.
- `corpus_related`: Contains tables related to corpora and their metadata.
- `user_related`: Contains tables related to users and their profiles.
- `agent_related`: Contains tables related to agents and their interactions.

## How to Use
Data models are defined using SQLAlchemy ORM. You can import the models and use them to interact with the database.
```python
from welearn_database.data.models import WeLearnDocument
```
Every model are accessible there, schema are handled under the hood.