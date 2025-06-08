import tzlocal

from backend.models.base import *


@dataclass
class ExecutionSession(BaseItem):
    __tablename__ = "execution_session"

    results: list = None

    # Initialize to None but it is non-nullable:
    request_id: Mapped[int] = mapped_column(Integer, ForeignKey("request.item_id", ondelete="SET NULL"), nullable=False, default=None)

    item_type: Mapped[str] = mapped_column(String, default="ExecutionSession")
    elapsed_time: Mapped[int] = mapped_column(String, default=0)
    timestamp: Mapped[datetime] = mapped_column(String, default=None)

    result: Mapped[str] = mapped_column(String, default="Running")
    iterations: Mapped[int] = mapped_column(Integer, default=0)
    total_ok: Mapped[int] = mapped_column(Integer, default=0)
    total_failed: Mapped[int] = mapped_column(Integer, default=0)
