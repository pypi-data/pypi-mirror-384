from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, func, types
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from welearn_database.data.enumeration import DbSchemaEnum
from welearn_database.data.models.document_related import WeLearnDocument

from . import Base

schema_name = DbSchemaEnum.USER_RELATED.value


class UserProfile(Base):
    __tablename__ = "user_profile"
    __table_args__ = {"schema": DbSchemaEnum.USER_RELATED.value}

    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )
    username: Mapped[str]
    email: Mapped[str]
    password_digest: Mapped[bytes]
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


class Bookmark(Base):
    __tablename__ = "bookmark"
    __table_args__ = {"schema": DbSchemaEnum.USER_RELATED.value}

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
    inferred_user_id = mapped_column(
        types.Uuid,
        ForeignKey(
            f"{DbSchemaEnum.USER_RELATED.value}.inferred_user.id",
            name="bookmark_inferred_user_id_fkey",
        ),
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
    inferred_user: Mapped["InferredUser"] = relationship()
    welearn_document: Mapped["WeLearnDocument"] = relationship()


class ChatMessage(Base):
    __tablename__ = "chat_message"
    __table_args__ = {"schema": DbSchemaEnum.USER_RELATED.value}

    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )
    user_id = mapped_column(
        types.Uuid,
        ForeignKey(f"{DbSchemaEnum.USER_RELATED.value}.user_profile.id"),
        nullable=False,
    )
    textual_content: Mapped[str]

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
    user: Mapped["UserProfile"] = relationship()


class ReturnedDocument(Base):
    __tablename__ = "returned_document"
    __table_args__ = {"schema": DbSchemaEnum.USER_RELATED.value}

    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )
    message_id = mapped_column(
        types.Uuid,
        ForeignKey(f"{DbSchemaEnum.USER_RELATED.value}.chat_message.id"),
        nullable=False,
    )
    document_id: Mapped[UUID] = mapped_column(
        types.Uuid,
        ForeignKey(
            f"{DbSchemaEnum.DOCUMENT_RELATED.value}.welearn_document.id",
            name="state_document_id_fkey",
        ),
        nullable=False,
    )
    welearn_document: Mapped["WeLearnDocument"] = relationship()
    chat_message: Mapped["ChatMessage"] = relationship()


class APIKeyManagement(Base):
    __tablename__ = "api_key_management"
    __table_args__ = {"schema": DbSchemaEnum.USER_RELATED.value}

    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )
    title: Mapped[str | None]
    register_email: Mapped[str]
    digest: Mapped[bytes]
    is_active: Mapped[bool]
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


class Session(Base):
    __tablename__ = "session"
    __table_args__ = {"schema": "user_related"}
    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )
    inferred_user_id: Mapped[UUID] = mapped_column(
        types.Uuid,
        ForeignKey("user_related.inferred_user.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=func.localtimestamp(),
        server_default="NOW()",
    )
    end_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=False)
    host: Mapped[str | None]
    user = relationship("InferredUser", foreign_keys=[inferred_user_id])


class InferredUser(Base):
    __tablename__ = "inferred_user"
    __table_args__ = {"schema": "user_related"}
    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=func.localtimestamp(),
        server_default="NOW()",
    )


class EndpointRequest(Base):
    __tablename__ = "endpoint_request"
    __table_args__ = {"schema": "user_related"}
    id: Mapped[UUID] = mapped_column(
        types.Uuid, primary_key=True, nullable=False, server_default="gen_random_uuid()"
    )
    session_id: Mapped[UUID] = mapped_column(
        types.Uuid,
        ForeignKey("user_related.session.id"),
        nullable=False,
    )
    endpoint_name: Mapped[str]
    http_code: Mapped[int]
    message: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=func.localtimestamp(),
        server_default="NOW()",
    )
    session = relationship("Session", foreign_keys=[session_id])
