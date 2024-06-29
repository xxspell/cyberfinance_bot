import asyncio

import aiosqlite
import json

async def export_sessions_to_json(db_path: str, output_file: str) -> None:
    async with aiosqlite.connect(database=db_path) as db:
        cursor = await db.execute("SELECT * FROM sessions")
        rows = await cursor.fetchall()

        sessions_data = []
        for row in rows:
            session_id, session_name, session_proxy, tg_web_data = row
            sessions_data.append({
                "session_id": session_id,
                "session_name": session_name,
                "session_proxy": session_proxy,
                "tg_web_data": tg_web_data
            })

    with open(output_file, 'w') as f:
        json.dump(sessions_data, f, indent=4)

# Usage example
asyncio.run(export_sessions_to_json('database/sessions.db', 'sessions_export.json'))