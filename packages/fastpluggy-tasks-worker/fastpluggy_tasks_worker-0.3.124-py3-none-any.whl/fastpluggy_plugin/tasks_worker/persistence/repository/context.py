from fastpluggy.core.database import session_scope
from fastpluggy.core.tools.serialize_tools import serialize_value
from ..models.context import TaskContextDB
from ...core.context import TaskContext


def save_context(ctx: TaskContext) -> int:
    """
    Persist a TaskContext to the database.
    If a context with the same task_id already exists, update it instead of inserting a new row.
    Returns the row id.
    """

    data = serialize_value(ctx)
    # Remove non-serializable/runtime-only fields if present
    data.pop('notifiers', None)

    with session_scope() as db:
        # Try to find an existing row by unique task_id
        existing = db.query(TaskContextDB).filter_by(task_id=ctx.task_id).one_or_none()
        if existing is None:
            row = TaskContextDB(**data)
            db.add(row)
            db.flush()
            return row.id
        else:
            # Update existing fields from data
            immutable_fields = {"id", "created_at", "updated_at"}
            for k, v in data.items():
                if k in immutable_fields:
                    continue
                if hasattr(existing, k):
                    setattr(existing, k, v)
            db.flush()
            return existing.id

