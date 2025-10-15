from datetime import datetime
from typing import Any
from urllib.parse import urlparse
from uuid import UUID
from zlib import adler32

from sqlalchemy import types, ForeignKey, UniqueConstraint, func, LargeBinary
from sqlalchemy.dialects.postgresql import TIMESTAMP, ENUM
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column, Mapped, relationship, validates

from welearn_database.modules.text_cleaning import clean_text
from welearn_database.data.enumeration import DbSchemaEnum, Step, Counter
from welearn_database.data.models.corpus_related import Corpus, NClassifierModel, BiClassifierModel, EmbeddingModel
from . import Base
from ...exceptions import InvalidURLScheme

schema_name = DbSchemaEnum.DOCUMENT_RELATED.value


class WeLearnDocument(Base):
    """
    This class represents a document in the WeLearn system.
    :cvar id: The unique identifier of the document.
    :cvar url: The URL of the document.
    :cvar title: The title of the document.
    :cvar lang: The language of the document.
    :cvar description: A brief description of the document.
    :cvar full_content: The full content of the document.
    :cvar details: Additional details about the document in JSON format.
    :cvar trace: An integer trace value for versioning or tracking changes.
    :cvar corpus_id: The database identifier of the corpus to which the document belongs.
    :cvar created_at: The timestamp when the document was created.
    :cvar updated_at: The timestamp when the document was last updated.
    :cvar corpus: The relationship to the Corpus object.
    """
    __tablename__ = "welearn_document"
    __table_args__ = (
        UniqueConstraint("url", name="welearn_document_url_key"),
        {"schema": schema_name},
    )

    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )
    url: Mapped[str] = mapped_column(nullable=False)
    title: Mapped[str | None]
    lang: Mapped[str | None]
    _description: Mapped[str]
    _full_content: Mapped[str]
    details: Mapped[dict[str, Any] | None]
    _trace: Mapped[int | None] = mapped_column(types.BIGINT)
    corpus_id: Mapped[UUID] = mapped_column(
        types.Uuid,
        ForeignKey(f"{DbSchemaEnum.CORPUS_RELATED.value}.corpus.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=func.localtimestamp(),
        server_default="NOW()",
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=func.localtimestamp(),
        server_default="NOW()",
        onupdate=func.localtimestamp(),
    )

    corpus: Mapped["Corpus"] = relationship("Corpus")

    @validates("url")
    def validate_url(self, key, value):
        """
        Validate the URL to ensure it has an accepted scheme (http or https).
        :param key:  The name of the attribute being validated.
        :param value:  The value of the URL to validate.
        :return:  The validated URL if it is valid.
        :raises InvalidURLScheme: If the URL scheme is not accepted or the URL is malformed
        """
        parsed_url = urlparse(url=value)
        accepted_scheme = ["https"]
        if parsed_url.scheme not in accepted_scheme or len(parsed_url.netloc) == 0:
            raise InvalidURLScheme(
                "There is an error on the URL form : %s", value
            )
        return value

    @validates("_full_content")
    def validate_full_content(self, key, value):
        """
        Validate the full content to ensure it meets the minimum length requirement.
        :param key:  The name of the attribute being validated.
        :param value:  The value of the full content to validate.
        :return:  The validated full content if it meets the length requirement.
        :raises ValueError: If the full content is too short.
        """
        if not value:
            raise ValueError("Full content cannot be empty or None")
        if len(value) < 25:
            raise ValueError(f"Content is too short : {len(value)}")
        return value

    @hybrid_property
    def full_content(self):
        return self._full_content

    @full_content.setter
    def full_content(self, full_content):
        self._full_content = clean_text(full_content)

    @hybrid_property
    def description(self):
        return self._description

    @description.setter
    def description(self, description):
        if not description:
            raise ValueError("Description cannot be empty or None")
        self._description = clean_text(description)

    @hybrid_property
    def trace(self):
        return adler32(bytes(self.full_content, "utf-8"))


class ProcessState(Base):
    """
    This class represents the state of a document processing step in the WeLearn system.
    :cvar id: The unique identifier of the process state.
    :cvar document_id: The identifier of the associated document.
    :cvar title: The title of the processing step, represented as an enumeration.
    :cvar created_at: The timestamp when the process state was created.
    :cvar operation_order: A bigint representing the order of operations for the process state.
    :cvar document: The relationship to the WeLearnDocument object.
    """
    __tablename__ = "process_state"
    __table_args__ = {"schema": DbSchemaEnum.DOCUMENT_RELATED.value}

    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )
    document_id: Mapped[UUID] = mapped_column(
        types.Uuid,
        ForeignKey(
            f"{DbSchemaEnum.DOCUMENT_RELATED.value}.welearn_document.id",
            name="state_document_id_fkey",
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        ENUM(*(e.value.lower() for e in Step), name="step", schema="document_related"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=func.localtimestamp(),
        server_default="NOW()",
    )
    operation_order = mapped_column(
        types.BIGINT,
        server_default="nextval('document_related.process_state_operation_order_seq'",
        nullable=False,
    )
    document: Mapped["WeLearnDocument"] = relationship()


class Keyword(Base):
    __tablename__ = "keyword"
    __table_args__ = (
        UniqueConstraint("keyword", name="keyword_unique"),
        {"schema": DbSchemaEnum.DOCUMENT_RELATED.value},
    )

    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )
    keyword: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=func.localtimestamp(),
        server_default="NOW()",
    )


class WeLearnDocumentKeyword(Base):
    __tablename__ = "welearn_document_keyword"
    __table_args__ = (
        UniqueConstraint(
            "welearn_document_id",
            "keyword_id",
            name="unique_welearn_document_keyword_association",
        ),
        {"schema": DbSchemaEnum.DOCUMENT_RELATED.value},
    )
    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )
    welearn_document_id: Mapped[UUID] = mapped_column(
        types.Uuid,
        ForeignKey(
            f"{DbSchemaEnum.DOCUMENT_RELATED.value}.welearn_document.id",
            name="state_document_id_fkey",
        ),
        nullable=False,
    )
    keyword_id: Mapped[UUID] = mapped_column(
        types.Uuid,
        ForeignKey(f"{DbSchemaEnum.DOCUMENT_RELATED.value}.keyword.id"),
        nullable=False,
    )


class ErrorRetrieval(Base):
    __tablename__ = "error_retrieval"
    __table_args__ = ({"schema": DbSchemaEnum.DOCUMENT_RELATED.value},)

    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )

    document_id: Mapped[UUID] = mapped_column(
        types.Uuid,
        ForeignKey(
            f"{DbSchemaEnum.DOCUMENT_RELATED.value}.welearn_document.id",
            name="state_document_id_fkey",
        ),
        nullable=False,
    )
    http_error_code: Mapped[int | None]
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=func.localtimestamp(),
        server_default="NOW()",
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=func.localtimestamp(),
        server_default="NOW()",
        onupdate=func.localtimestamp(),
    )
    error_info: Mapped[str]

    document: Mapped["WeLearnDocument"] = relationship()


class DocumentSlice(Base):
    __tablename__ = "document_slice"
    __table_args__ = {"schema": DbSchemaEnum.DOCUMENT_RELATED.value}

    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )
    document_id: Mapped[UUID] = mapped_column(
        types.Uuid,
        ForeignKey(
            f"{DbSchemaEnum.DOCUMENT_RELATED.value}.welearn_document.id",
            name="state_document_id_fkey",
        ),
        nullable=False,
    )
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary)
    body: Mapped[str | None]
    order_sequence: Mapped[int]
    embedding_model_name: Mapped[str]

    embedding_model_id = mapped_column(
        types.Uuid,
        ForeignKey(f"{DbSchemaEnum.CORPUS_RELATED.value}.embedding_model.id"),
        nullable=False,
    )

    document: Mapped["WeLearnDocument"] = relationship()
    embedding_model: Mapped["EmbeddingModel"] = relationship()


class AnalyticCounter(Base):
    __tablename__ = "analytic_counter"
    __table_args__ = {
        "schema": DbSchemaEnum.DOCUMENT_RELATED.value,
    }

    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )
    document_id: Mapped[UUID] = mapped_column(
        types.Uuid,
        ForeignKey(
            f"{DbSchemaEnum.DOCUMENT_RELATED.value}.welearn_document.id",
            name="state_document_id_fkey",
        ),
        nullable=False,
    )
    counter_name: Mapped[Counter]
    counter_value: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=func.localtimestamp(),
        server_default="NOW()",
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=func.localtimestamp(),
        server_default="NOW()",
        onupdate=func.localtimestamp(),
    )
    document: Mapped["WeLearnDocument"] = relationship()



class CorpusEmbeddingModel(Base):
    __tablename__ = "corpus_embedding_model"
    __table_args__ = (
        UniqueConstraint(
            "corpus_id",
            "embedding_model_id",
            name="unique_corpus_embedding_association",
        ),
        {"schema": DbSchemaEnum.CORPUS_RELATED.value},
    )

    corpus_id = mapped_column(
        types.Uuid,
        ForeignKey(f"{DbSchemaEnum.CORPUS_RELATED.value}.corpus.id"),
        primary_key=True,
    )
    embedding_model_id = mapped_column(
        types.Uuid,
        ForeignKey(f"{DbSchemaEnum.CORPUS_RELATED.value}.embedding_model.id"),
        primary_key=True,
    )

    used_since: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=func.localtimestamp(),
        server_default="NOW()",
    )

    embedding_model: Mapped["EmbeddingModel"] = relationship()
    corpus: Mapped["Corpus"] = relationship()


class CorpusNClassifierModel(Base):
    __tablename__ = "corpus_n_classifier_model"
    __table_args__ = (
        UniqueConstraint(
            "corpus_id",
            "n_classifier_model_id",
            name="unique_corpus_n_classifier_association",
        ),
        {"schema": DbSchemaEnum.CORPUS_RELATED.value},
    )

    corpus_id = mapped_column(
        types.Uuid,
        ForeignKey(f"{DbSchemaEnum.CORPUS_RELATED.value}.corpus.id"),
        primary_key=True,
    )
    n_classifier_model_id = mapped_column(
        types.Uuid,
        ForeignKey(f"{DbSchemaEnum.CORPUS_RELATED.value}.n_classifier_model.id"),
        primary_key=True,
    )

    used_since: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=func.localtimestamp(),
        server_default="NOW()",
    )

    n_classifier_model: Mapped["NClassifierModel"] = relationship()
    corpus: Mapped["Corpus"] = relationship()


class CorpusBiClassifierModel(Base):
    __tablename__ = "corpus_bi_classifier_model"
    __table_args__ = (
        UniqueConstraint(
            "corpus_id",
            "bi_classifier_model_id",
            name="unique_corpus_bi_classifier_association",
        ),
        {"schema": DbSchemaEnum.CORPUS_RELATED.value},
    )

    corpus_id = mapped_column(
        types.Uuid,
        ForeignKey(f"{DbSchemaEnum.CORPUS_RELATED.value}.corpus.id"),
        primary_key=True,
    )
    bi_classifier_model_id = mapped_column(
        types.Uuid,
        ForeignKey(f"{DbSchemaEnum.CORPUS_RELATED.value}.bi_classifier_model.id"),
        primary_key=True,
    )
    used_since: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=func.localtimestamp(),
        server_default="NOW()",
    )

    bi_classifier_model: Mapped["BiClassifierModel"] = relationship()
    corpus: Mapped["Corpus"] = relationship()


class Sdg(Base):
    __tablename__ = "sdg"
    __table_args__ = {"schema": DbSchemaEnum.DOCUMENT_RELATED.value}

    id: Mapped[UUID] = mapped_column(
        types.Uuid,
        primary_key=True,
        nullable=False,
        server_default="gen_random_uuid()",
    )
    slice_id = mapped_column(
        types.Uuid,
        ForeignKey(
            f"{DbSchemaEnum.DOCUMENT_RELATED.value}.document_slice.id",
            name="sdg_slice_id_fkey2",
        ),
        nullable=False,
    )
    sdg_number: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=func.localtimestamp(),
        server_default="NOW()",
    )

    bi_classifier_model_id = mapped_column(
        types.Uuid,
        ForeignKey(f"{DbSchemaEnum.CORPUS_RELATED.value}.bi_classifier_model.id"),
    )
    n_classifier_model_id = mapped_column(
        types.Uuid,
        ForeignKey(f"{DbSchemaEnum.CORPUS_RELATED.value}.n_classifier_model.id"),
    )
    bi_classifier_model: Mapped["BiClassifierModel"] = relationship()
    n_classifier_model: Mapped["NClassifierModel"] = relationship()
    slice: Mapped["DocumentSlice"] = relationship()