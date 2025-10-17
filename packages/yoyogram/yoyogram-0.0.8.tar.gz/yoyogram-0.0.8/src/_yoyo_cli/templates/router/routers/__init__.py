import importlib
from src import yoyo

from aiogram import Dispatcher, Router


def register_routers(dp: Dispatcher):
    # Register middlewares of dispatcher (global middlewares)

    # Include routers to dispatcher
    routers_list = yoyo.tools.listdir(__file__)
    routers_list.remove("__init__.py")
    try:
        routers_list.remove("__pycache__")
    except ValueError:
        pass

    routers: list[tuple[int, Router]] = []


    package = yoyo.tools.package(__file__)
    for module in routers_list:
        import_get_router = importlib.import_module(f".{module}", package=package).get_router
        router.append(import_get_router())

        max_i = max(i for i, _ in routers if i != -1) + 1
        for _, router in sorted(routers, key=lambda x: max_i if x[0] == -1 else x[0]):
            dp.include_router(router)