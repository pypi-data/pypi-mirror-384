from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sqlalchemy_utils.types import UUIDType


class Base(AsyncAttrs, DeclarativeBase):
    """Base model"""

    pass


class ContextInformation(Base):
    """Contains information about the context"""

    __tablename__ = "context_information"

    id: Mapped[int] = mapped_column(primary_key=True)

    context_id: Mapped[bytes] = mapped_column(UUIDType(binary=True))
    """The id (uuid as bytes)"""

    object_id: Mapped[str] = mapped_column(String(256))
    """The object in this context"""

    parent_id: Mapped[str | None] = mapped_column(String(256), default=None)
    """id of the post, that was replied to"""
