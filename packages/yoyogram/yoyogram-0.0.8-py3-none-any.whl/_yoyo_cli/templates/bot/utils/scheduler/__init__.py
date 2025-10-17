import importlib
import yoyo

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from tgbot.bots.{bot_name}.config import get_config

scheduler: AsyncIOScheduler


def register_scheduler(bot: Bot):
    global scheduler
    scheduler = AsyncIOScheduler(timezone=get_config().misc.tz)

    tasks = list(map(lambda x: x[:-3], yoyo.tools.listdir(__file__)))
    try:
        tasks.remove('__init__')
        tasks.remove('__pycach')
    except ValueError:
        pass

    package = yoyo.tools.package(__file__)
    for module in tasks:
        import_register = importlib.import_module(f'.{module}', package=package).register
        import_register(scheduler, bot)

    scheduler.start()