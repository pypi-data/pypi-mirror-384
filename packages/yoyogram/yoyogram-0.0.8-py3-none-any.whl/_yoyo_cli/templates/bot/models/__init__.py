import importlib
from copy import deepcopy
import yoyo


async def connect_models():
    python_models = yoyo.tools.listdir(__file__)

    for el in deepcopy(python_models):
        if not el[-3:] == ".py":
            python_models.remove(el)
    python_models.remove("__init__.py")
    python_models = list(map(lambda x: x[:-3], python_models))

    package = yoyo.tools.package(__file__)

    for module in python_models:
        import_connect = importlib.import_module(f".{module}", package=package).main
        await import_connect()
