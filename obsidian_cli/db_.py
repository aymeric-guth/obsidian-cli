import asyncio
import pathlib

import aiosql

queries = aiosql.from_path(pathlib.Path(__file__).parent / "sql", "sqlite3")


async def main():
    async with aiosqlite.connect(":memory:") as conn:
        # Parallel queries!
        greetings, user = await asyncio.gather(
            queries.get_all_greetings(conn),
            queries.get_user_by_username(conn, username="willvaughn"),
        )

        for _, greeting in greetings:
            print(f"{greeting}, {user[2]}!")


asyncio.run(main())

# file, every non-md file
# path, name, ext
# note, md file
# path, name

# link
# relation note -> file | note

# tag
# name

# tag_file
# note -> tag
