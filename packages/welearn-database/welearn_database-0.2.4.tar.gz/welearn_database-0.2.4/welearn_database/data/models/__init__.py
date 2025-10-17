from datetime import datetime
from typing import Any

from sqlalchemy import types
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase


@compiles(ARRAY, "sqlite")
def compile_binary_sqlite(type_, compiler, **kw):
    return "TEXT"


class Base(DeclarativeBase):
    type_annotation_map = {
        dict[str, Any]: types.JSON,
        datetime: TIMESTAMP(timezone=False),
        float: types.NUMERIC,
    }

    def __setattr__(self, name, value):
        """
        Raise an exception if attempting to assign to an atribute of a "read-only" object
        Transient attributes need to be prefixed with "_t_"
        """
        if (
            getattr(self, "__read_only__", False)
            and name != "_sa_instance_state"
            and not name.startswith("_t_")
        ):
            raise ValueError(
                "Trying to assign to %s of a read-only object %s" % (name, self)
            )
        super(Base, self).__setattr__(name, value)


from .corpus_related import *
from .document_related import *
from .user_related import *
