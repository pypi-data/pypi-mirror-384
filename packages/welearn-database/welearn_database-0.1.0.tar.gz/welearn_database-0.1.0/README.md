# WeLearn Database

This repository contains the database schema and sample data for the WeLearn application, an online learning platform.

## Pypi Package
You can install this pacakge via pypi :

```bash
pip install welearn-database
```

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