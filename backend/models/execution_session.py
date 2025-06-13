import tzlocal

from backend.models.base import *


@dataclass
class ExecutionSession(BaseItem):
    __tablename__ = "execution_session"

    results: list = None
    iterations: int = 0
    total_ok: int = 0
    total_failed: int = 0

    # Initialize to None but it is non-nullable:
    request_id: Mapped[int] = mapped_column(Integer, ForeignKey("request.item_id", ondelete="SET NULL"), nullable=False, default=None)

    item_type: Mapped[str] = mapped_column(String, default="ExecutionSession")
    elapsed_time: Mapped[int] = mapped_column(String, default=0)
    timestamp: Mapped[datetime] = mapped_column(String, default=None)

    result: Mapped[str] = mapped_column(String, default="Running")

