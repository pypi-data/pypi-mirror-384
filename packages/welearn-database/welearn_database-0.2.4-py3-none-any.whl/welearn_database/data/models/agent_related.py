from typing import Any, Dict, Optional

from sqlalchemy import Index, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import text
from sqlalchemy.types import LargeBinary, Integer

from welearn_database.data.enumeration import DbSchemaEnum
from welearn_database.data.models import Base


schema_name = DbSchemaEnum.AGENT_RELATED.value


class CheckpointBlobs(Base):
    __tablename__ = "checkpoint_blobs"
    __table_args__ = (
        Index("checkpoint_blobs_thread_id_idx", "thread_id"),
        {"schema": schema_name},
    )

    thread_id: Mapped[str] = mapped_column(Text, primary_key=True, nullable=False)
    checkpoint_ns: Mapped[str] = mapped_column(
        Text, server_default=text("''::text"), primary_key=True, nullable=False
    )
    channel: Mapped[str] = mapped_column(Text, primary_key=True, nullable=False)
    version_: Mapped[str] = mapped_column("version", Text, primary_key=True, nullable=False)
    type_: Mapped[str] = mapped_column("type", Text, nullable=False)
    blob: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)


class CheckpointMigrations(Base):
    __tablename__ = "checkpoint_migrations"
    __table_args__ = {"schema": schema_name},

    v: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)


class CheckpointWrites(Base):
    __tablename__ = "checkpoint_writes"
    __table_args__ = (
        Index("checkpoint_writes_thread_id_idx", "thread_id"),
        {"schema": schema_name},
    )

    thread_id: Mapped[str] = mapped_column(Text, primary_key=True, nullable=False)
    checkpoint_ns: Mapped[str] = mapped_column(
        Text, server_default=text("''::text"), primary_key=True, nullable=False
    )
    checkpoint_id: Mapped[str] = mapped_column(Text, primary_key=True, nullable=False)
    task_id: Mapped[str] = mapped_column(Text, primary_key=True, nullable=False)
    idx: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)

    channel: Mapped[str] = mapped_column(Text, nullable=False)
    type_: Mapped[Optional[str]] = mapped_column("type", Text, nullable=True)
    blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    task_path: Mapped[str] = mapped_column(
        Text, server_default=text("''::text"), nullable=False
    )


class Checkpoints(Base):
    __tablename__ = "checkpoints"
    __table_args__ = {"schema": schema_name},

    thread_id: Mapped[str] = mapped_column(Text, primary_key=True, nullable=False)
    checkpoint_ns: Mapped[str] = mapped_column(
        Text, server_default=text("''::text"), primary_key=True, nullable=False
    )
    checkpoint_id: Mapped[str] = mapped_column(Text, primary_key=True, nullable=False)

    parent_checkpoint_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type_: Mapped[Optional[str]] = mapped_column("type", Text, nullable=True)
    checkpoint: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    metadata_: Mapped[Dict[str, Any]] = mapped_column("metadata",
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
