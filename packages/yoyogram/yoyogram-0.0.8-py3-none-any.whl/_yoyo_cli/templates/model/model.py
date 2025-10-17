
import aiosqlite as asql
from aiosqlite import Connection


class {capital_name}:
    _db: Connection
    name = r"{db_path}"

    @classmethod
    async def connect(cls):
        cls._db = await asql.connect(cls.name)
        c = await cls._db.cursor()
        await c.execute("""CREATE TABLE IF NOT EXISTS {name}Table ();""")
        await cls._db.commit()


async def main():
    await {capital_name}.connect()
