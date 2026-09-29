import aiosqlite
from config import DB_NAME

class Database:
    @staticmethod
    async def init():
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            await db.execute("""CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                name TEXT NOT NULL,
                url TEXT,
                platform TEXT,
                posting_type TEXT,
                status TEXT DEFAULT 'new',
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )""")
            await db.commit()

    # ===== PROJECTS CRUD =====
    @staticmethod
    async def create_project(name: str) -> int:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute("INSERT INTO projects (name) VALUES (?)", (name,))
            await db.commit()
            return cursor.lastrowid

    @staticmethod
    async def get_all_projects():
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT id, name FROM projects ORDER BY created_at DESC") as cursor:
                return await cursor.fetchall()

    @staticmethod
    async def get_project(project_id: int):
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT id, name FROM projects WHERE id=?", (project_id,)) as cursor:
                return await cursor.fetchone()

    @staticmethod
    async def update_project_name(project_id: int, new_name: str):
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE projects SET name=? WHERE id=?", (new_name, project_id))
            await db.commit()

    @staticmethod
    async def delete_project(project_id: int):
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("DELETE FROM sources WHERE project_id=?", (project_id,))
            await db.execute("DELETE FROM projects WHERE id=?", (project_id,))
            await db.commit()

    # ===== SOURCES CRUD =====
    @staticmethod
    async def create_source(project_id: int, name: str, url: str, platform: str, posting_type: str, note: str):
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                "INSERT INTO sources (project_id, name, url, platform, posting_type, note) VALUES (?, ?, ?, ?, ?, ?)",
                (project_id, name, url, platform, posting_type, note)
            )
            await db.commit()
            return cursor.lastrowid

    @staticmethod
    async def get_sources_by_project(project_id: int):
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute(
                "SELECT id, name, url, platform, posting_type, status, note FROM sources WHERE project_id=? ORDER BY created_at DESC",
                (project_id,)
            ) as cursor:
                return await cursor.fetchall()

    @staticmethod
    async def get_source(source_id: int):
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute(
                    # Добавили project_id вторым параметром
                    "SELECT id, project_id, name, url, platform, posting_type, status, note FROM sources WHERE id=?",
                    (source_id,)
            ) as cursor:
                return await cursor.fetchone()

    @staticmethod
    async def update_source_status(source_id: int, new_status: str):
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE sources SET status=? WHERE id=?", (new_status, source_id))
            await db.commit()

    @staticmethod
    async def update_source_note(source_id: int, new_note: str):
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE sources SET note=? WHERE id=?", (new_note, source_id))
            await db.commit()

    @staticmethod
    async def delete_source(source_id: int):
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("DELETE FROM sources WHERE id=?", (source_id,))
            await db.commit()