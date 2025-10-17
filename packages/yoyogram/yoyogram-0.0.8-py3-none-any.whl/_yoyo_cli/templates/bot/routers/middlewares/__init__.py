
from aiogram import Dispatcher


def register_dp_middlewares(dp: Dispatcher):
	"""
	Strict order
	dp.message.middleware.register(YourMiddleware())
	"""
	...
