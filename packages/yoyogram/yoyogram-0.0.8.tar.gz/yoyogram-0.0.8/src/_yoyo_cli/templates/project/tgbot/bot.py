from aiogram import Bot, Dispatcher

from tgbot.bots import build_bots, start_bots


async def build() -> list[tuple[Bot, Dispatcher]]:
    from tgbot.models import connect_models
    await connect_models()

    return await build_bots()


async def start(bots: list[tuple[Bot, Dispatcher]]):
    await start_bots(bots)


async def main():
    await start(await build())