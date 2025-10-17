import importlib
import yoyo

from aiogram import Bot, Dispatcher


async def build_bots() -> list[tuple[Bot, Dispatcher]]:
    bots_list = yoyo.tools.listdir(__file__)
    bots_list.remove("__init__.py")
    try:
        bots_list.remove("__pycache__")
    except:
        pass

    bots: list[tuple[Bot, Dispatcher]] = []

    package = yoyo.tools.package(__file__)

    for module in bots_list:
        import_build_bot = importlib.import_module(f".{module}", package=package).build_bot
        bots.append(import_build_bot())

    return bots


async def start_bots(bots: list[tuple[Bot, Dispatcher]]):
    bots_list = yoyo.tools.listdir(__file__)


    bots_list.remove("__init__.py")
    try:
        bots_list.remove("__pycache__")
    except:
        pass

    package = yoyo.tools.package(__file__)

    for module, bot_dp in zip(bots_list, bots):
        bot, dp = bot_dp
        import_start_bot = importlib.import_module(f".{module}", package=package).start
        await import_start_bot(bot, dp)
