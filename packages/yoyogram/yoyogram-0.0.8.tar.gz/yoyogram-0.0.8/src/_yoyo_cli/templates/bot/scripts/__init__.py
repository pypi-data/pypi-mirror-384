from aiogram import Bot, Dispatcher

"""  
Public Scripts to use it for any routers,  
or to call it from other pieces of structure,  
like another code (not tgbot)
"""

bot: Bot
dp: Dispatcher


def register_scripts(work_bot: Bot, work_dp: Dispatcher):
    global bot, dp

    bot = work_bot
    dp = work_dp


__all__ = ['register_scripts', 'bot', 'dp']
