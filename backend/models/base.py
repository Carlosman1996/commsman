from dataclasses import dataclass
from datetime import datetime, timezone
from email.policy import default

from sqlalchemy import Integer, String, ForeignKey, Column, Boolean, JSON, DateTime
from sqlalchemy.orm import Mapped, MappedAsDataclass, DeclarativeBase, relationship, declared_attr
from sqlalchemy.testing.schema import mapped_column


@dataclass
class Item:
    id: int
    item_handler: str


class Base(MappedAsDataclass, DeclarativeBase):
    pass


@dataclass
class BaseItem(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, init=False)
    name: Mapped[str] = mapped_column(String)
    item_handler: Mapped[str] = mapped_column(String, init=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, init=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.now(timezone.utc), init=False)
    modified_by: Mapped[str] = mapped_column(String, init=False)

    def __post_init__(self):
        self.item_handler = self.__class__.__name__
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.modified_by = "Ordillan"


@dataclass
class BaseRequest(BaseItem):
    __abstract__ = True

    item_response_handler: str = None
    client: object = None
    run_options: object = None

    parent_id: Mapped[int] = mapped_column(Integer, ForeignKey('collection.id'), nullable=True, default=None)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey('client.id'), nullable=True, default=None)
    run_options_id: Mapped[int] = mapped_column(Integer, ForeignKey('run_options.id'), nullable=True, default=None)

    position: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    client_type: Mapped[str] = mapped_column(String, default="No connection")


@dataclass
class BaseResult(BaseItem):
    __abstract__ = True

    parent_id: Mapped[int] = mapped_column(Integer, ForeignKey('collection_result.id'), nullable=True)

    client_type: Mapped[str] = mapped_column(String)
    result: Mapped[str] = mapped_column(String)
    elapsed_time: Mapped[int] = mapped_column(String)
    timestamp: Mapped[datetime] = mapped_column(String)

    error_message: Mapped[str] = mapped_column(String)
