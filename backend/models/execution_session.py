import tzlocal

from backend.models.base import *


@dataclass
class ExecutionSession(BaseItem):
    __tablename__ = "execution_session"

    results: list = None

    item_type: Mapped[str] = mapped_column(String, default="ExecutionSession")
    elapsed_time: Mapped[int] = mapped_column(String, default=0)
    timestamp: Mapped[datetime] = mapped_column(String, default=datetime.now(tzlocal.get_localzone()))

    total_ok: Mapped[int] = mapped_column(Integer, default=0)
    total_failed: Mapped[int] = mapped_column(Integer, default=0)
    total_pending: Mapped[int] = mapped_column(Integer, default=0)
