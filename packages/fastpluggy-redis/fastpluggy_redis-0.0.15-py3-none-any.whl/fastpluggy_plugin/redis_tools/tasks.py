from tasks_worker import TaskWorker


@TaskWorker.register()
async def task_flush_db(db: int):
    from .redis_connector import RedisConnection, get_redis_connection
    redis_conn: RedisConnection = get_redis_connection(db=db)
    success = redis_conn.flush_db()
    return {"success": success}
