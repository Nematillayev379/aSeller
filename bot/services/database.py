import aiosqlite
from typing import Optional
from bot.config import DATABASE_PATH


class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        await self._create_tables()

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def _create_tables(self):
        await self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS ads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                image_file_id TEXT,
                title TEXT,
                price INTEGER DEFAULT 0,
                description TEXT DEFAULT '',
                source TEXT DEFAULT 'manual',
                external_id TEXT DEFAULT '',
                product_url TEXT DEFAULT '',
                is_posted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                address TEXT,
                comment TEXT,
                ad_id INTEGER,
                product_name TEXT,
                product_price INTEGER DEFAULT 0,
                prepay_percent INTEGER DEFAULT 100,
                prepay_amount INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE,
                channel_name TEXT,
                is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            CREATE TABLE IF NOT EXISTS admin_users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await self.conn.commit()

    async def set_setting(self, key: str, value: str):
        await self.conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        await self.conn.commit()

    async def get_setting(self, key: str) -> Optional[str]:
        cursor = await self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row["value"] if row else None

    async def add_ad(self, user_id: int, image_file_id: str, title: str,
                     price: int, description: str = "", source: str = "manual",
                     external_id: str = "", product_url: str = "") -> bool:
        try:
            await self.conn.execute(
                """INSERT INTO ads (user_id, image_file_id, title, price, description, source, external_id, product_url)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, image_file_id, title, price, description, source, external_id, product_url)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"DB xatosi: {e}")
            return False

    async def get_unposted_ads(self, limit: int = 1) -> list:
        cursor = await self.conn.execute("SELECT * FROM ads WHERE is_posted = 0 ORDER BY created_at DESC LIMIT ?", (limit,))
        return await cursor.fetchall()

    async def get_all_ads(self, limit: int = 50) -> list:
        cursor = await self.conn.execute("SELECT * FROM ads ORDER BY created_at DESC LIMIT ?", (limit,))
        return await cursor.fetchall()

    async def mark_ad_posted(self, ad_id: int):
        await self.conn.execute("UPDATE ads SET is_posted = 1 WHERE id = ?", (ad_id,))
        await self.conn.commit()

    async def delete_ad(self, ad_id: int):
        await self.conn.execute("DELETE FROM ads WHERE id = ?", (ad_id,))
        await self.conn.commit()

    async def add_order(self, user_id: int, username: str, full_name: str, phone: str,
                        address: str, comment: str, ad_id: int, product_name: str,
                        product_price: int, prepay_percent: int, prepay_amount: int) -> bool:
        try:
            await self.conn.execute(
                """INSERT INTO orders (user_id, username, full_name, phone, address, comment,
                   ad_id, product_name, product_price, prepay_percent, prepay_amount)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, username, full_name, phone, address, comment,
                 ad_id, product_name, product_price, prepay_percent, prepay_amount)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"DB xatosi: {e}")
            return False

    async def get_pending_orders(self) -> list:
        cursor = await self.conn.execute("SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at DESC")
        return await cursor.fetchall()

    async def get_all_orders(self, limit: int = 50) -> list:
        cursor = await self.conn.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,))
        return await cursor.fetchall()

    async def update_order_status(self, order_id: int, status: str):
        await self.conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await self.conn.commit()

    async def add_channel(self, channel_id: str, channel_name: str) -> bool:
        try:
            await self.conn.execute("INSERT OR REPLACE INTO channels (channel_id, channel_name, is_active) VALUES (?, ?, 1)", (channel_id, channel_name))
            await self.conn.commit()
            return True
        except Exception:
            return False

    async def remove_channel(self, channel_id: str):
        await self.conn.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
        await self.conn.commit()

    async def get_active_channels(self) -> list:
        cursor = await self.conn.execute("SELECT * FROM channels WHERE is_active = 1")
        return await cursor.fetchall()

    async def get_all_channels(self) -> list:
        cursor = await self.conn.execute("SELECT * FROM channels ORDER BY channel_name")
        return await cursor.fetchall()

    async def toggle_channel(self, channel_id: str):
        cursor = await self.conn.execute("SELECT is_active FROM channels WHERE channel_id = ?", (channel_id,))
        row = await cursor.fetchone()
        if row:
            new_status = 0 if row["is_active"] else 1
            await self.conn.execute("UPDATE channels SET is_active = ? WHERE channel_id = ?", (new_status, channel_id))
            await self.conn.commit()

    async def get_ad_stats(self) -> dict:
        cursor = await self.conn.execute("SELECT COUNT(*) as total FROM ads")
        total = (await cursor.fetchone())["total"]
        cursor = await self.conn.execute("SELECT COUNT(*) as posted FROM ads WHERE is_posted = 1")
        posted = (await cursor.fetchone())["posted"]
        cursor = await self.conn.execute("SELECT COUNT(*) as unposted FROM ads WHERE is_posted = 0")
        unposted = (await cursor.fetchone())["unposted"]
        return {"total": total, "posted": posted, "unposted": unposted}

    async def get_order_stats(self) -> dict:
        cursor = await self.conn.execute("SELECT COUNT(*) as total FROM orders")
        total = (await cursor.fetchone())["total"]
        cursor = await self.conn.execute("SELECT COUNT(*) as pending FROM orders WHERE status = 'pending'")
        pending = (await cursor.fetchone())["pending"]
        cursor = await self.conn.execute("SELECT COUNT(*) as completed FROM orders WHERE status = 'completed'")
        completed = (await cursor.fetchone())["completed"]
        return {"total": total, "pending": pending, "completed": completed}

    async def add_admin_user(self, user_id: int, username: str, full_name: str) -> bool:
        try:
            await self.conn.execute("INSERT OR REPLACE INTO admin_users (user_id, username, full_name) VALUES (?, ?, ?)", (user_id, username, full_name))
            await self.conn.commit()
            return True
        except Exception:
            return False

    async def remove_admin_user(self, user_id: int):
        await self.conn.execute("DELETE FROM admin_users WHERE user_id = ?", (user_id,))
        await self.conn.commit()

    async def is_admin_user(self, user_id: int) -> bool:
        cursor = await self.conn.execute("SELECT 1 FROM admin_users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone() is not None

    async def get_all_admin_users(self) -> list:
        cursor = await self.conn.execute("SELECT * FROM admin_users ORDER BY added_at DESC")
        return await cursor.fetchall()


db = Database()
