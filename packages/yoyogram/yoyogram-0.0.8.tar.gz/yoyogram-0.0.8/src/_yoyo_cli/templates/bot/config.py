from dataclasses import dataclass
from environs import Env
from yoyo.logger import Logger


@dataclass
class Tgbot:
    token: str
    admins: list[int]
    use_redis: bool
    use_webhook: bool


@dataclass
class Redis:
    host: str
    port: int
    password: str
    is_prefix: bool
    prefix: str


@dataclass
class Webhook:
    url: str


@dataclass
class Payment:
    token: str
    currency: str


@dataclass
class Misc:
    tz: str


@dataclass
class Config:
    tgbot: Tgbot
    redis: Redis
    payment: Payment
    misc: Misc


def get_config() -> Config:
    env = Env()
    path = './tgbot/bots/{bot_name}/.env'
    env.read_env(path)

    return Config(
        tgbot=Tgbot(
            token=env.str("TOKEN"),
            admins=list(map(int, env.str("ADMINS").split(' '))),
            use_redis=env.bool("USE_REDIS"),
            use_webhook=env.bool("USE_WEBHOOK"),
        ),
        redis=Redis(
            host=env.str("REDIS_HOST"),
            port=env.int("REDIS_PORT"),
            password=env.str("REDIS_PASSWORD"),
            is_prefix=env.bool("REDIS_IS_PREFIX"),
            prefix=env.str("REDIS_PREFIX"),
        ),
        payment=Payment(
            token=env.str("PAYMENT_PROVIDER_TOKEN"),
            currency=env.str("PAYMENT_CURRENCY"),
        ),
        misc=Misc(
            tz=env.str("SCHEDULER_TZ")
        )
    )


log = Logger()
