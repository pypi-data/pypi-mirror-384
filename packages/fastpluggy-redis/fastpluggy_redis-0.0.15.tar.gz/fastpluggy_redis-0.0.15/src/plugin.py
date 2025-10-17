# plugin.py
from typing import Annotated, Any

from fastpluggy.core.module_base import FastPluggyBaseModule
from fastpluggy.core.tools.inspect_tools import InjectDependency

from .config import RedisToolsSettings

def get_redis_router():
    from .router import redis_router
    return redis_router

class RedisToolsPlugin(FastPluggyBaseModule):
    module_name: str = "redis_tools"
    module_version: str = "0.0.11"

    module_menu_name: str = "Redis Tools"
    module_menu_icon:str = "fa-solid fa-database"
    module_menu_type: str = "main"

    module_settings: Any = RedisToolsSettings
    module_router: Any = get_redis_router

    depends_on: dict = {
        "ui_tools": ">=0.0.2",
    }

    optional_dependencies: dict = {
        "tasks_worker": ">=0.1.0",
    }

    def on_load_complete(self, fast_pluggy: Annotated["FastPluggy", InjectDependency]) -> None:
        pass