import importlib
import yoyo

from aiogram import Router


def register_handlers(router: Router):
    modules: list[str] = list(map(lambda x: x[:-3], yoyo.tools.listdir(__file__)))
    modules.remove('__init__')
    try:
        modules.remove('__pycach')
    except ValueError:
        pass

    package = yoyo.tools.package(__file__)
    for module in modules:
        import_register = importlib.import_module(f".{module}", package=package).register
        import_register(router)
