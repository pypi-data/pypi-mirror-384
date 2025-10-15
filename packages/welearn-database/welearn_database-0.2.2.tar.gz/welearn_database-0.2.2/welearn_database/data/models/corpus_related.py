from datetime import datetime
from uuid import UUID

from sqlalchemy import types, ForeignKey, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import mapped_column, Mapped

from . import Base
from welearn_database.data.enumeration import DbSchemaEnum

schema_name = DbSchemaEnum.CORPUS_RELATED.value

class Corpus(Base):
    __tablename__ = "corpus"
    __table_args__ = {"schema": schema_name}

    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )
    source_name: Mapped[str]
    is_fix: Mapped[bool]
    binary_treshold: Mapped[float] = mapped_column(nullable=False, default=0.5)
    is_active: Mapped[bool]
    category_id: Mapped[UUID] = mapped_column(
        types.Uuid,
        ForeignKey(f"{schema_name}.category.id"),
    )

class Category(Base):
    __tablename__ = "category"
    __table_args__ = {"schema": schema_name}

    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )
    title: Mapped[str]


class EmbeddingModel(Base):
    __tablename__ = "embedding_model"
    __table_args__ = {"schema": schema_name}

    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )
    title: Mapped[str]
    lang: Mapped[str]


class BiClassifierModel(Base):
    __tablename__ = "bi_classifier_model"
    __table_args__ = {"schema": schema_name}

    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )
    title: Mapped[str]
    binary_treshold: Mapped[float] = mapped_column(default=0.5)
    lang: Mapped[str]
    used_since: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=func.localtimestamp(),
        server_default="NOW()",
    )


class NClassifierModel(Base):
    __tablename__ = "n_classifier_model"
    __table_args__ = {"schema": schema_name}

    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )
    title: Mapped[str]
    lang: Mapped[str]
    treshold_sdg_1: Mapped[float] = mapped_column(default=0.5)
    treshold_sdg_2: Mapped[float] = mapped_column(default=0.5)
    treshold_sdg_3: Mapped[float] = mapped_column(default=0.5)
    treshold_sdg_4: Mapped[float] = mapped_column(default=0.5)
    treshold_sdg_5: Mapped[float] = mapped_column(default=0.5)
    treshold_sdg_6: Mapped[float] = mapped_column(default=0.5)
    treshold_sdg_7: Mapped[float] = mapped_column(default=0.5)
    treshold_sdg_8: Mapped[float] = mapped_column(default=0.5)
    treshold_sdg_9: Mapped[float] = mapped_column(default=0.5)
    treshold_sdg_10: Mapped[float] = mapped_column(default=0.5)
    treshold_sdg_11: Mapped[float] = mapped_column(default=0.5)
    treshold_sdg_12: Mapped[float] = mapped_column(default=0.5)
    treshold_sdg_13: Mapped[float] = mapped_column(default=0.5)
    treshold_sdg_14: Mapped[float] = mapped_column(default=0.5)
    treshold_sdg_15: Mapped[float] = mapped_column(default=0.5)
    treshold_sdg_16: Mapped[float] = mapped_column(default=0.5)
    used_since: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=func.localtimestamp(),
        server_default="NOW()",
    )

class CorpusNameEmbeddingModelLang(Base):
    __tablename__ = "corpus_name_embedding_model_lang"
    __table_args__ = {"schema": schema_name}
    __read_only__ = True
    source_name : Mapped[str]= mapped_column(primary_key=True)
    title: Mapped[str]
    lang: Mapped[str]

