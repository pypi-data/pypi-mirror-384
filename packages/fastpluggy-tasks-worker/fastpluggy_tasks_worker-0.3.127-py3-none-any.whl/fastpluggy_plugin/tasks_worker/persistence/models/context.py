
from sqlalchemy import Column, String, Boolean, Integer, JSON, Index

from fastpluggy.core.database import Base


class TaskContextDB(Base):
    __tablename__ = "fp_task_contexts"
    __table_args__ = (
        Index("ix_fp_task_contexts_task_id", "task_id", unique=True),
        Index("ix_fp_task_contexts_parent_task_id", "parent_task_id"),
        Index("ix_fp_task_contexts_task_name", "task_name"),
        {"extend_existing": True},
    )

    # Base provides: id (PK), created_at, updated_at

    task_id = Column(String(200), nullable=False)
    parent_task_id = Column(String(200), nullable=True)

    task_name = Column(String(200), nullable=False)
    func_name = Column(String(200), nullable=False)

    args = Column(JSON, default=list, nullable=False)
    kwargs = Column(JSON, default=dict, nullable=False)

    # Keep compat field even if not fully used in new context
    notifier_config = Column(JSON, default=list, nullable=False)

    max_retries = Column(Integer, default=0, nullable=False)
    retry_delay = Column(Integer, default=0, nullable=False)

    task_origin = Column(String(200), default="unk", nullable=False)
    topic = Column(String(200), nullable=True)
    allow_concurrent = Column(Boolean, default=True, nullable=False)
    task_type = Column(String(200), default=None, nullable=True)

    extra_context = Column(JSON, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return self._repr(
            id=self.id,
            task_id=self.task_id,
            task_name=self.task_name,
            func_name=self.func_name,
        )
