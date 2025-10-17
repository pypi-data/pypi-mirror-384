from fastapi import APIRouter, HTTPException
from typing import Optional

from fastpluggy_plugin.tasks_worker import TaskWorker
from fastpluggy.core.tools.serialize_tools import serialize_value

api_broker_router = APIRouter(
    prefix='/api/broker',
    tags=['broker']
)


@api_broker_router.get("/stats", name="broker_stats")
async def get_broker_stats():
    """
    Get general broker statistics and information.
    """
    try:
        # Access the broker through the task worker
        broker = TaskWorker._get_broker()
        if not broker:
            raise HTTPException(status_code=500, detail="Broker not available")
        
        stats = broker.stats()
        return serialize_value(stats)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve broker stats: {str(e)}")


@api_broker_router.get("/workers", name="broker_workers")
async def get_workers(include_tasks: bool = False, stale_after: Optional[float] = None):
    """
    Get list of workers connected to the broker.
    
    Args:
        include_tasks: Include list of tasks for each worker
        stale_after: Consider workers stale after this many seconds
    """
    try:
        broker = TaskWorker._get_broker()
        if not broker:
            raise HTTPException(status_code=500, detail="Broker not available")
        
        workers = broker.get_workers(include_tasks=include_tasks, stale_after=stale_after)
        return serialize_value({"workers": workers})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve workers: {str(e)}")


@api_broker_router.get("/topics", name="broker_topics")
async def get_topics():
    """
    Get list of topics with queue metrics.
    """
    try:
        broker = TaskWorker._get_broker()
        if not broker:
            raise HTTPException(status_code=500, detail="Broker not available")
        
        topics = broker.get_topics()
        return serialize_value({"topics": topics})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve topics: {str(e)}")


@api_broker_router.get("/cluster", name="broker_cluster_stats")
async def get_cluster_stats():
    """
    Get aggregate cluster-level statistics.
    """
    try:
        broker = TaskWorker._get_broker()
        if not broker:
            raise HTTPException(status_code=500, detail="Broker not available")
        
        cluster_stats = broker.get_cluster_stats()
        return serialize_value(cluster_stats)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cluster stats: {str(e)}")


@api_broker_router.get("/active-tasks", name="broker_active_tasks")
async def get_active_tasks(topic: Optional[str] = None):
    """
    Get list of active tasks (queued and in-flight).
    
    Args:
        topic: Filter by specific topic, or get all topics if None
    """
    try:
        broker = TaskWorker._get_broker()
        if not broker:
            raise HTTPException(status_code=500, detail="Broker not available")
        
        active_tasks = broker.get_all_active_tasks(topic)
        return serialize_value({"active_tasks": active_tasks, "topic": topic})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve active tasks: {str(e)}")


@api_broker_router.get("/locks", name="broker_locks")
async def get_locks():
    """
    Get list of current task locks (for exclusive tasks).
    """
    try:
        broker = TaskWorker._get_broker()
        if not broker:
            raise HTTPException(status_code=500, detail="Broker not available")
        
        locks = broker.get_locks()
        return serialize_value({"locks": locks})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve locks: {str(e)}")


@api_broker_router.post("/locks/{task_id}/release", name="broker_release_lock")
async def force_release_lock(task_id: str):
    """
    Force release a task lock if supported by the broker.
    
    Args:
        task_id: The ID of the task whose lock should be released
    """
    try:
        broker = TaskWorker._get_broker()
        if not broker:
            raise HTTPException(status_code=500, detail="Broker not available")
        
        success = broker.force_release_lock(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Lock not found or could not be released")
        
        return serialize_value({"task_id": task_id, "released": success})
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to release lock: {str(e)}")