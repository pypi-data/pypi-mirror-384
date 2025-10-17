import importlib
import os
import yoyo

from aiogram import Router

from .middlewares import register_middlewares
from .handlers import register_handlers


def get_router() -> tuple[int, Router]:
    router = Router(name=yoyo.tools.basename(__file__))

    # Register middlewares, handlers and errors
    register_middlewares(router)
    register_handlers(router)

    # Include to router another routers
    path = yoyo.tools.listpath(__file__)
    path.append("routers")
    try:
        routers = os.listdir("\\".join(path))
        package = yoyo.tools.package(path)
        for module in routers:
            import_get_router = importlib.import_module(f".{module}", package=package).get_router
            router.include_router(import_get_router())
    except (FileNotFoundError, TypeError):
        pass

    return {router_index}, router
