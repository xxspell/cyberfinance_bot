import asyncio

import aiosqlite
from urllib.parse import urlparse

async def modify_proxy_scheme() -> None:
    async with aiosqlite.connect(database='database/sessions.db') as db:
        cursor = await db.execute("SELECT id, session_proxy FROM sessions")
        async for row in cursor:
            proxy_id, proxy_url = row
            parsed_url = urlparse(proxy_url)
            if parsed_url.scheme == 'socks5':
                new_proxy_url = f"http://{parsed_url.netloc}"
                await db.execute(
                    "UPDATE sessions SET session_proxy = ? WHERE id = ?",
                    (new_proxy_url, proxy_id)
                )
        await db.commit()

# Run the script
asyncio.run(modify_proxy_scheme())