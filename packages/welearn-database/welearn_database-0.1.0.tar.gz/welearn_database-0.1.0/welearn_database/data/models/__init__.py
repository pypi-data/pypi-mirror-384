from datetime import datetime
from typing import Any

from sqlalchemy import types
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    type_annotation_map = {
        dict[str, Any]: types.JSON,
        datetime: TIMESTAMP(timezone=False),
        float: types.NUMERIC,
    }

from .document_related import *
from .corpus_related import *
from .user_related import *