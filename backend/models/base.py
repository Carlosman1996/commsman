from dataclasses import dataclass
from datetime import datetime, timezone

import tzlocal
from sqlalchemy import Integer, String, ForeignKey, Column, Boolean, JSON, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, MappedAsDataclass, DeclarativeBase
from sqlalchemy.testing.schema import mapped_column


class Base(MappedAsDataclass, DeclarativeBase):
    pass


@dataclass
class BaseItem(Base):
    __abstract__ = True

    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, init=False)
    name: Mapped[str] = mapped_column(String)
    item_handler: Mapped[str] = mapped_column(String, init=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, init=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.now(tzlocal.get_localzone()), init=False)
    modified_by: Mapped[str] = mapped_column(String, init=False)

    parent: object = None
    children: list = None

    def __post_init__(self):
        self.item_handler = self.__class__.__name__
        self.created_at = datetime.now(tzlocal.get_localzone())
        self.updated_at = datetime.now(tzlocal.get_localzone())
        self.modified_by = "Ordillan"
        self.children = []


@dataclass
class BaseRequest(BaseItem):
    __abstract__ = True

    item_response_handler: str = None
    client: object = None
    run_options: object = None
    last_result: object = None
    results_history: list = None

    parent_id: Mapped[int] = mapped_column(Integer, ForeignKey("collection.item_id", ondelete="CASCADE"), nullable=True, default=None)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("client.item_id"), nullable=True, default=None)  # TODO: delete if request is removed
    run_options_id: Mapped[int] = mapped_column(Integer, ForeignKey("run_options.item_id"), nullable=True, default=None)  # TODO: delete if request is removed

    position: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    client_type: Mapped[str] = mapped_column(String, default="No connection")


@dataclass
class BaseResult(BaseItem):
    __abstract__ = True

    execution_session_id: Mapped[int] = mapped_column(Integer, ForeignKey("execution_session.item_id", ondelete="CASCADE"), nullable=False, default=None)
    parent_id: Mapped[int] = mapped_column(Integer, ForeignKey("collection_result.item_id", ondelete="SET NULL"), nullable=True, default=None)
    request_id: Mapped[int] = mapped_column(Integer, ForeignKey("request.item_id", ondelete="SET NULL"), nullable=True, default=None)

    client_type: Mapped[str] = mapped_column(String, nullable=False, default=None)
    result: Mapped[str] = mapped_column(String, nullable=False, default=None)
    elapsed_time: Mapped[int] = mapped_column(String, nullable=False, default=None)
    timestamp: Mapped[datetime] = mapped_column(String, nullable=False, default=None)

    error_message: Mapped[str] = mapped_column(String, default=None)
