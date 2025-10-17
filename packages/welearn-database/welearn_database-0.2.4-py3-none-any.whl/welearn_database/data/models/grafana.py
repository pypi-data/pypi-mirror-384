import uuid
from datetime import datetime

from sqlalchemy import UUID
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from welearn_database.data.enumeration import DbSchemaEnum, Step
from welearn_database.data.models import Base

schema_name = DbSchemaEnum.GRAFANA.value


class Corpus(Base):
    __tablename__ = "corpus"
    __table_args__ = {"schema": schema_name}
    __read_only__ = True

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    source_name: Mapped[str] = mapped_column()
    is_fix: Mapped[bool | None] = mapped_column(nullable=True)
    binary_treshold: Mapped[float | None] = mapped_column(nullable=True)

class DocumentLatestState(Base):
    __tablename__ = "document_latest_state"
    __table_args__ = {"schema": schema_name}
    __read_only__ = True

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    corpus_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    lang: Mapped[str | None] = mapped_column(nullable=True)
    title: Mapped[str] = mapped_column(
        ENUM(*(e.value.lower() for e in Step), name="step", schema="document_related"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column()
    operation_order: Mapped[int] = mapped_column()


class DocumentStateSummary(Base):
    __tablename__ = "document_state_summary"
    __table_args__ = {"schema": schema_name}
    __read_only__ = True

    source_name: Mapped[str] = mapped_column(primary_key=True)

    url_retrieved_count: Mapped[int] = mapped_column()
    document_scraped_count: Mapped[int] = mapped_column()
    document_is_irretrievable_count: Mapped[int] = mapped_column()
    document_vectorized_count: Mapped[int] = mapped_column()
    document_classified_sdg_count: Mapped[int] = mapped_column()
    document_classified_non_sdg_count: Mapped[int] = mapped_column()
    document_in_qdrant_count: Mapped[int] = mapped_column()
    kept_for_trace_count: Mapped[int] = mapped_column()
    no_state_count: Mapped[int] = mapped_column()
    total_documents: Mapped[int] = mapped_column()


class EndpointRequest(Base):
    __tablename__ = "endpoint_request"
    __table_args__ = {"schema": schema_name}
    __read_only__ = True

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    endpoint_name: Mapped[str] = mapped_column()
    http_code: Mapped[int | None] = mapped_column(nullable=True)
    message: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column()


class InferredUser(Base):
    __tablename__ = "inferred_user"
    __table_args__ = {"schema": schema_name}
    __read_only__ = True

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    created_at: Mapped[datetime] = mapped_column()


class ProcessState(Base):
    __tablename__ = "process_state"
    __table_args__ = {"schema": schema_name}
    __read_only__ = True

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    title: Mapped[str] = mapped_column(
        ENUM(*(e.value.lower() for e in Step), name="step", schema="document_related"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column()
    operation_order: Mapped[int] = mapped_column()

class QtyEndpointsPerUser(Base):
    __tablename__ = "qty_endpoints_per_user"
    __table_args__ = {"schema": schema_name}
    __read_only__ = True

    count: Mapped[int] = mapped_column(primary_key=True)


class QtySessionEndpointPerUser(Base):
    __tablename__ = "qty_session_endpoint_per_user"
    __table_args__ = {"schema": schema_name}
    __read_only__ = True

    inferred_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    host: Mapped[str] = mapped_column(primary_key=True)
    count_sessions: Mapped[int] = mapped_column()
    count_endpoints: Mapped[int] = mapped_column()


class QtySessionUserPerHost(Base):
    __tablename__ = "qty_session_user_per_host"
    __table_args__ = {"schema": schema_name}
    __read_only__ = True

    host: Mapped[str] = mapped_column(primary_key=True)
    count_sessions: Mapped[int] = mapped_column()
    count_users: Mapped[int] = mapped_column()


class Session(Base):
    __tablename__ = "session"
    __table_args__ = {"schema": schema_name}
    __read_only__ = True

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    inferred_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column()
    end_at: Mapped[datetime | None] = mapped_column(nullable=True)
    host: Mapped[str | None] = mapped_column(nullable=True)
