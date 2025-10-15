import logging
import math
import os
from typing import Any, List

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


def create_db_session():
    engine = create_sqlalchemy_engine()
    session_made = sessionmaker(engine)
    return session_made()


def create_sqlalchemy_engine():
    pg_driver = os.getenv("PG_DRIVER", "postgresql+psycopg2")
    pg_user = os.getenv("PG_USER")
    pg_password = os.getenv("PG_PASSWORD")
    pg_host = os.getenv("PG_HOST")
    pg_port = os.getenv("PG_PORT")
    pg_db = os.getenv("PG_DB")
    url_object = URL.create(
        drivername=pg_driver,
        username=pg_user,
        password=pg_password,
        host=pg_host,
        port=pg_port,
        database=pg_db,
    )
    engine = create_engine(url_object)
    return engine
