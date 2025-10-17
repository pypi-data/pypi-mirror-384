from aiogram import Bot
from aiogram.types import BotCommand


async def register_my_commands(bot: Bot):
    return await bot.set_my_commands(
        [
            BotCommand(
                command="start",
                description="Starts bot"
            )
        ]
    )
