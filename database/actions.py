import aiosqlite


async def add_session(session_name: str,
                      session_proxy: str = '') -> None:
    async with aiosqlite.connect(database='database/sessions.db') as db:
        await db.execute(sql='INSERT INTO sessions (session_name, session_proxy) VALUES (?, ?)',
                         parameters=(session_name, session_proxy))
        await db.commit()


async def get_session_proxy_by_name(session_name: str) -> str | None:
    async with aiosqlite.connect(database='database/sessions.db') as db:
        async with db.execute(sql='SELECT session_proxy FROM sessions WHERE session_name = ?',
                              parameters=(session_name,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None


async def get_tg_web_data_by_name(session_name: str) -> str | None:
    async with aiosqlite.connect(database='database/sessions.db') as db:
        async with db.execute(sql='SELECT tg_web_data FROM sessions WHERE session_name = ?',
                              parameters=(session_name,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None

async def set_field_by_name(session_name: str, field_name: str, field_value: str) -> None:
    async with aiosqlite.connect(database='database/sessions.db') as db:
        await db.execute(
            sql=f'UPDATE sessions SET {field_name} = ? WHERE session_name = ?',
            parameters=(field_value, session_name)
        )
        await db.commit()


async def check_and_rename_column(session_name):
    db_path = f'sessions/{session_name}'  # Путь к базе SQLite
    async with aiosqlite.connect(db_path) as db:
        # Проверяем, существует ли колонка 'number' в таблице 'version'
        cursor = await db.execute("PRAGMA table_info(version)")
        columns = await cursor.fetchall()
        if ('number',) in columns:
            # Переименовываем колонку 'number' в 'version'
            await db.execute("ALTER TABLE version RENAME COLUMN number TO version")
            await db.commit()
            # print("Колонка 'number' успешно переименована в 'version'")
        else:
            print("Колонка 'number' не существует в таблице 'version'")
