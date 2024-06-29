import asyncio
import os
import aiosqlite


async def update_sessions_from_files(folder_path: str, proxy_file: str) -> None:
    if not os.path.exists(proxy_file):
        print(f"Proxy file '{proxy_file}' does not exist.")
        return

    with open(proxy_file, 'r') as f:
        proxies = f.readlines()

    # Remove whitespace and empty lines from proxies list
    proxies = [proxy.strip() for proxy in proxies if proxy.strip()]

    async with aiosqlite.connect(database='database/sessions.db') as db:
        # Get a list of all files in the folder
        files = os.listdir(folder_path)
        # Get existing session names from the database
        existing_sessions = set()
        cursor = await db.execute("SELECT session_name FROM sessions")
        async for row in cursor:
            existing_sessions.add(row[0])

        # Iterate through files in the folder
        for file_name in files:
            # Check if the filename exists in the database
            basename, extension = os.path.splitext(file_name)
            if basename not in existing_sessions:

                session_proxy = proxies.pop(0).strip() if proxies else None
                # If not, insert a new record into the database
                await db.execute(
                    "INSERT INTO sessions (session_name, session_proxy) VALUES (?, ?)",
                    (file_name, session_proxy)
                )

                if session_proxy:
                    with open(proxy_file, 'w') as f:
                        f.write('\n'.join(proxies))

        await db.commit()


asyncio.run(update_sessions_from_files("sessions", r"C:\dd.txt"))