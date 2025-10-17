# redis_browser.py
import logging

from fastapi import APIRouter, Depends, Request, Query, Body
from fastapi.responses import HTMLResponse
from starlette import status
from starlette.responses import RedirectResponse

from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.flash import FlashMessage
from fastpluggy.core.widgets import CustomTemplateWidget, TableWidget, ButtonListWidget, ButtonWidget
from fastpluggy_plugin.ui_tools.extra_widget.layout.grid import GridWidget
from .redis_connector import RedisConnection, get_redis_connection
from .schema import RedisCommandRequest, RedisCommandResponse
from .stats_card_tools import get_stats_cards

# Create router
redis_router = APIRouter()


# Define routes
@redis_router.get("/", response_class=HTMLResponse, name="redis_browser")
async def redis_browser(request: Request, view_builder=Depends(get_view_builder)):
    stats_cards = []
    try:
        redis_conn: RedisConnection = get_redis_connection()
        info = redis_conn.client_info()
        stats_cards = get_stats_cards(info=info)

    except Exception as err:
        logging.warning(f"Error when getting info: {err}")

    return view_builder.generate(
        request,
        title=f"Redis Browser",
        widgets=[
            GridWidget.create_responsive_grid(widgets=stats_cards,
                                              cols_sm=1,
                                              cols_md=6,
                                              cols_lg=6,
                                              cols_xl=6,
                                              ),
            CustomTemplateWidget(
                template_name='redis_tools/browser.html.j2',
                context={
                    "base_plugin_url": str(request.url_for("redis_browser"))[:-1]
                }
            )
        ]
    )


@redis_router.get("/slowlog")
async def get_slowlog(
        request: Request,
        db: int = Query(None, description="Database index to use"),
        count: int = Query(128, ge=1, le=1024, description="Max number of slowlog entries to fetch"),
        view_builder=Depends(get_view_builder)
):
    redis_conn: RedisConnection = get_redis_connection(db=db)
    slow_logs = redis_conn.get_slow_logs(count=count)
    return view_builder.generate(
        request,
        title=f"Redis slow logs",
        widgets=[
            ButtonListWidget(buttons=[
                ButtonWidget(label="Reset slow logs", url=str(request.url_for("reset_slowlog")),
                             css_class="btn btn-danger")
            ]),
            TableWidget(data=slow_logs),
            ButtonListWidget(buttons=[ButtonWidget(label="Back to redis", url=str(request.url_for("redis_browser")))])
        ]
    )


@redis_router.get("/slowlog/reset")
async def reset_slowlog(request: Request, db: int = Query(None, description="Database index to use")):
    """
    Clear all entries from the Redis slowlog (SLOWLOG RESET).
    """
    redis_conn: RedisConnection = get_redis_connection(db=db)
    success = redis_conn.reset_slow_logs()
    if success:
        FlashMessage.add(request, message="Slow logs reset successfully!")
    else:
        FlashMessage.add(request, message="Failed to reset slow logs!", type="error")

    return RedirectResponse(url=request.url_for('get_slowlog'), status_code=status.HTTP_303_SEE_OTHER)


@redis_router.get("/databases")
async def get_databases(redis_conn: RedisConnection = Depends(get_redis_connection)):
    """Get a list of all available Redis databases."""
    return redis_conn.get_databases()


@redis_router.post("/databases/{db_index}")
async def select_database(db_index: int, redis_conn: RedisConnection = Depends(get_redis_connection)):
    """Select a Redis database."""
    success = redis_conn.select_db(db_index)
    return {"success": success, "db_index": db_index}


@redis_router.get("/keys")
async def get_keys(
        pattern: str = "*",
        db: int = Query(None, description="Database index to use"),
):
    redis_conn: RedisConnection = get_redis_connection(db=db)

    return redis_conn.get_keys(pattern)


@redis_router.get("/keys/{key:path}")
async def get_key(
        key: str,
        db: int = Query(None, description="Database index to use"),
):
    redis_conn: RedisConnection = get_redis_connection(db=db)

    return redis_conn.get_key_details(key)


@redis_router.delete("/keys/{key:path}")
async def delete_key(
        key: str,
        db: int = Query(None, description="Database index to use"),
):
    redis_conn: RedisConnection = get_redis_connection(db=db)
    success = redis_conn.delete_key(key)
    return {"success": success}


@redis_router.post("/flush-db")
async def flush_db(
        db: int = Query(None, description="Database index to use"),
):
    redis_conn: RedisConnection = get_redis_connection(db=db)
    success = redis_conn.flush_db()
    return {"success": success}


@redis_router.get("/raw-command", response_class=HTMLResponse, name="redis_raw_command")
async def redis_raw_command(request: Request, view_builder=Depends(get_view_builder)):
    """
    Display a page for executing raw Redis commands.
    """
    return view_builder.generate(
        request,
        title="Redis Raw Command",
        widgets=[
            ButtonListWidget(buttons=[
                ButtonWidget(label="Back to Redis Browser", url=str(request.url_for("redis_browser")))
            ]),
            CustomTemplateWidget(
                template_name='redis_tools/raw_command.html.j2',
                context={
                    "base_plugin_url": str(request.url_for("redis_browser"))[:-1]
                }
            )
        ]
    )


@redis_router.post("/raw-command", response_model=RedisCommandResponse)
async def execute_raw_command(
        command_request: RedisCommandRequest = Body(...),
):
    """
    Execute a raw Redis command.
    """
    redis_conn: RedisConnection = get_redis_connection(db=command_request.db)
    try:
        result = redis_conn.execute_raw_command(command_request.command)
        return RedisCommandResponse(
            command=command_request.command,
            result=result,
            error=None
        )
    except Exception as e:
        return RedisCommandResponse(
            command=command_request.command,
            result=None,
            error=str(e)
        )
