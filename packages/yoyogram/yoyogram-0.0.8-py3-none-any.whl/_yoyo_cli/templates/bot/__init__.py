import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import setup_application
from aiohttp import web
from redis import Redis

from tgbot.bots.{bot_name}.config import get_config


def build() -> tuple[Bot, Dispatcher]:
    config = get_config()

    bot = Bot(
        token=config.tgbot.token
    )

    if config.tgbot.use_redis:
        redis = Redis(
            host=config.redis.host,
            port=config.redis.port,
            password=config.redis.password
        )
        key_builder = None
        if config.redis.is_prefix:
            key_builder = DefaultKeyBuilder(prefix=config.redis.prefix)
        storage = RedisStorage(redis, key_builder=key_builder)
    else:
        storage = MemoryStorage()

    dp = Dispatcher(
        storage=storage
    )

    from tgbot.bots.{bot_name}.scripts import register_scripts
    register_scripts(bot, dp)
    from tgbot.bots.{bot_name}.utils.scheduler import register_scheduler
    register_scheduler(bot)
    from tgbot.bots.{bot_name}.routers import register_routers
    register_routers(dp)

    return bot, dp


async def start(bot: Bot, dp: Dispatcher):
    from tgbot.bots.{bot_name}.models import connect_models
    await connect_models()

    from tgbot.bots.{bot_name}.utils.menu import register_my_commands
    await register_my_commands(bot)

    config = get_config()

    if config.tgbot.use_webhook:

        async def on_startup(app):
            await bot.set_webhook(app["webhook_url"])

        async def on_cleanup(app):
            await bot.delete_webhook()
            await dp.storage.close()
            await bot.session.close()

        app = web.Application()
        app["bot"] = bot
        app["dp"] = dp
        app["webhook_url"] = config.webhook.url

        setup_application(app, dp, bot=bot)
        app.on_startup.append(on_startup)
        app.on_cleanup.append(on_cleanup)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8080)
        await site.start()

        try:
            await asyncio.Event().wait()
        finally:
            await runner.cleanup()

    else:
        try:
            await dp.start_polling(bot)
        finally:
            await dp.storage.close()
            await bot.session.close()


__all__ = ['build', 'start']
