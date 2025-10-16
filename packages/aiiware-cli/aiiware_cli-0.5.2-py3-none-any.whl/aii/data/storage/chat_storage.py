"""Chat Storage - SQLite-based persistent storage for chat history"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite

from ...core.context.models import ChatContext, ChatMessage


class ChatStorage:
    """SQLite-based storage for chat history"""

    def __init__(self, db_path: Path | None = None):
        """Initialize chat storage"""
        if db_path is None:
            db_path = Path.home() / ".aii" / "chats.db"

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize database schema"""
        if self._initialized:
            return

        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS chats (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    archived BOOLEAN DEFAULT FALSE
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS chat_tags (
                    chat_id TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    PRIMARY KEY (chat_id, tag),
                    FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    function_name TEXT NOT NULL,
                    parameters TEXT DEFAULT '{}',
                    result TEXT DEFAULT '{}',
                    timestamp TIMESTAMP NOT NULL,
                    success BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
                );

                -- Indexes for performance
                CREATE INDEX IF NOT EXISTS idx_chats_updated_at ON chats (updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_chats_archived ON chats (archived);
                CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages (chat_id);
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages (timestamp);
                CREATE INDEX IF NOT EXISTS idx_chat_tags_tag ON chat_tags (tag);
                CREATE INDEX IF NOT EXISTS idx_executions_chat_id ON executions (chat_id);
            """
            )
            await db.commit()

        self._initialized = True

    async def save_chat(self, context: ChatContext) -> bool:
        """Save chat context to database"""
        await self.initialize()

        try:
            async with aiosqlite.connect(str(self.db_path)) as db:
                # Save or update chat
                await db.execute(
                    """
                    INSERT OR REPLACE INTO chats (id, title, created_at, updated_at, metadata, archived)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        context.chat_id,
                        context.title,
                        context.created_at.isoformat(),
                        context.updated_at.isoformat(),
                        json.dumps(context.metadata),
                        context.archived,
                    ),
                )

                # Clear existing messages and tags for this chat
                await db.execute(
                    "DELETE FROM messages WHERE chat_id = ?", (context.chat_id,)
                )
                await db.execute(
                    "DELETE FROM chat_tags WHERE chat_id = ?", (context.chat_id,)
                )

                # Save messages
                for message in context.messages:
                    await db.execute(
                        """
                        INSERT INTO messages (chat_id, message_id, role, content, timestamp, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            context.chat_id,
                            message.message_id,
                            message.role,
                            message.content,
                            message.timestamp.isoformat(),
                            json.dumps(message.metadata),
                        ),
                    )

                # Save tags
                for tag in context.tags:
                    await db.execute(
                        """
                        INSERT INTO chat_tags (chat_id, tag)
                        VALUES (?, ?)
                    """,
                        (context.chat_id, tag),
                    )

                await db.commit()
                return True

        except Exception as e:
            print(f"Error saving chat {context.chat_id}: {e}")
            return False

    async def load_chat(
        self, chat_id: str, message_limit: int = 0
    ) -> ChatContext | None:
        """Load chat context from database"""
        await self.initialize()

        try:
            async with aiosqlite.connect(str(self.db_path)) as db:
                db.row_factory = aiosqlite.Row

                # Load chat metadata
                async with db.execute(
                    """
                    SELECT id, title, created_at, updated_at, metadata, archived
                    FROM chats WHERE id = ?
                """,
                    (chat_id,),
                ) as cursor:
                    chat_row = await cursor.fetchone()

                if not chat_row:
                    return None

                # Load messages
                if message_limit > 0:
                    message_query = """
                        SELECT message_id, role, content, timestamp, metadata
                        FROM messages WHERE chat_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """
                    params = (chat_id, message_limit)
                else:
                    message_query = """
                        SELECT message_id, role, content, timestamp, metadata
                        FROM messages WHERE chat_id = ?
                        ORDER BY timestamp ASC
                    """
                    params = (chat_id,)

                messages = []
                async with db.execute(message_query, params) as cursor:
                    rows = await cursor.fetchall()
                    for row in rows:
                        message = ChatMessage(
                            role=row["role"],
                            content=row["content"],
                            timestamp=datetime.fromisoformat(row["timestamp"]),
                            metadata=json.loads(row["metadata"] or "{}"),
                            message_id=row["message_id"],
                        )
                        messages.append(message)

                # Reverse if we limited messages (we got them in DESC order)
                if message_limit > 0:
                    messages.reverse()

                # Load tags (ordered consistently)
                tags = []
                async with db.execute(
                    """
                    SELECT tag FROM chat_tags WHERE chat_id = ? ORDER BY tag
                """,
                    (chat_id,),
                ) as cursor:
                    rows = await cursor.fetchall()
                    tags = [row["tag"] for row in rows]

                # Create context
                context = ChatContext(
                    chat_id=chat_row["id"],
                    title=chat_row["title"],
                    created_at=datetime.fromisoformat(chat_row["created_at"]),
                    updated_at=datetime.fromisoformat(chat_row["updated_at"]),
                    messages=messages,
                    metadata=json.loads(chat_row["metadata"] or "{}"),
                    tags=tags,
                    archived=bool(chat_row["archived"]),
                )

                return context

        except Exception as e:
            print(f"Error loading chat {chat_id}: {e}")
            return None

    async def list_chats(
        self,
        limit: int = 50,
        offset: int = 0,
        since: datetime | None = None,
        archived: bool = False,
    ) -> list[dict[str, Any]]:
        """List chats with pagination and filtering"""
        await self.initialize()

        try:
            query = """
                SELECT c.id, c.title, c.created_at, c.updated_at, c.archived,
                       COUNT(m.id) as message_count
                FROM chats c
                LEFT JOIN messages m ON c.id = m.chat_id
                WHERE c.archived = ?
            """
            params = [archived]

            if since:
                query += " AND c.updated_at >= ?"
                params.append(since.isoformat())

            query += """
                GROUP BY c.id
                ORDER BY c.updated_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            async with aiosqlite.connect(str(self.db_path)) as db:
                db.row_factory = aiosqlite.Row

                chats = []
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    for row in rows:
                        # Load tags for this chat (ordered consistently)
                        tags = []
                        async with db.execute(
                            """
                            SELECT tag FROM chat_tags WHERE chat_id = ? ORDER BY tag
                        """,
                            (row["id"],),
                        ) as tag_cursor:
                            tag_rows = await tag_cursor.fetchall()
                            tags = [tag_row["tag"] for tag_row in tag_rows]

                        chats.append(
                            {
                                "id": row["id"],
                                "title": row["title"],
                                "message_count": row["message_count"],
                                "created_at": row["created_at"],
                                "updated_at": row["updated_at"],
                                "archived": row["archived"],
                                "tags": tags,
                            }
                        )

                return chats

        except Exception as e:
            print(f"Error listing chats: {e}")
            return []

    async def search_chats(
        self,
        query: str,
        search_content: bool = False,
        tag_filter: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Search chats by title, content, or tags"""
        await self.initialize()

        try:
            # Build base query
            base_query = """
                SELECT DISTINCT c.id, c.title, c.created_at, c.updated_at, c.archived,
                       COUNT(m.id) as message_count
                FROM chats c
                LEFT JOIN messages m ON c.id = m.chat_id
            """

            conditions = []
            params = []

            # Search in title
            if query:
                conditions.append("c.title LIKE ?")
                params.append(f"%{query}%")

            # Search in content if requested
            if search_content and query:
                conditions.append("m.content LIKE ?")
                params.append(f"%{query}%")

            # Tag filter
            if tag_filter:
                base_query += " LEFT JOIN chat_tags ct ON c.id = ct.chat_id"
                conditions.append("ct.tag = ?")
                params.append(tag_filter)

            # Combine conditions
            if conditions:
                base_query += " WHERE " + " OR ".join(conditions)

            base_query += """
                GROUP BY c.id
                ORDER BY c.updated_at DESC
                LIMIT ?
            """
            params.append(limit)

            async with aiosqlite.connect(str(self.db_path)) as db:
                db.row_factory = aiosqlite.Row

                chats = []
                async with db.execute(base_query, params) as cursor:
                    rows = await cursor.fetchall()
                    for row in rows:
                        # Load tags (ordered consistently)
                        tags = []
                        async with db.execute(
                            """
                            SELECT tag FROM chat_tags WHERE chat_id = ? ORDER BY tag
                        """,
                            (row["id"],),
                        ) as tag_cursor:
                            tag_rows = await tag_cursor.fetchall()
                            tags = [tag_row["tag"] for tag_row in tag_rows]

                        chats.append(
                            {
                                "id": row["id"],
                                "title": row["title"],
                                "message_count": row["message_count"],
                                "created_at": row["created_at"],
                                "updated_at": row["updated_at"],
                                "archived": row["archived"],
                                "tags": tags,
                            }
                        )

                return chats

        except Exception as e:
            print(f"Error searching chats: {e}")
            return []

    async def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat and all associated data"""
        await self.initialize()

        try:
            async with aiosqlite.connect(str(self.db_path)) as db:
                await db.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
                await db.commit()
                return True

        except Exception as e:
            print(f"Error deleting chat {chat_id}: {e}")
            return False

    async def archive_chat(self, chat_id: str, archived: bool = True) -> bool:
        """Archive or unarchive a chat"""
        await self.initialize()

        try:
            async with aiosqlite.connect(str(self.db_path)) as db:
                await db.execute(
                    """
                    UPDATE chats SET archived = ? WHERE id = ?
                """,
                    (archived, chat_id),
                )
                await db.commit()
                return True

        except Exception as e:
            print(f"Error archiving chat {chat_id}: {e}")
            return False

    async def update_chat_metadata(
        self,
        chat_id: str,
        title: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Update chat metadata"""
        await self.initialize()

        try:
            async with aiosqlite.connect(str(self.db_path)) as db:
                # Update basic fields
                if title is not None:
                    await db.execute(
                        """
                        UPDATE chats SET title = ?, updated_at = ? WHERE id = ?
                    """,
                        (title, datetime.now().isoformat(), chat_id),
                    )

                if metadata is not None:
                    await db.execute(
                        """
                        UPDATE chats SET metadata = ?, updated_at = ? WHERE id = ?
                    """,
                        (json.dumps(metadata), datetime.now().isoformat(), chat_id),
                    )

                # Update tags
                if tags is not None:
                    await db.execute(
                        "DELETE FROM chat_tags WHERE chat_id = ?", (chat_id,)
                    )
                    for tag in tags:
                        await db.execute(
                            """
                            INSERT INTO chat_tags (chat_id, tag) VALUES (?, ?)
                        """,
                            (chat_id, tag),
                        )

                await db.commit()
                return True

        except Exception as e:
            print(f"Error updating chat metadata {chat_id}: {e}")
            return False

    async def get_chat_stats(self) -> dict[str, Any]:
        """Get statistics about stored chats"""
        await self.initialize()

        try:
            async with aiosqlite.connect(str(self.db_path)) as db:
                db.row_factory = aiosqlite.Row

                stats = {}

                # Total chats
                async with db.execute("SELECT COUNT(*) as count FROM chats") as cursor:
                    row = await cursor.fetchone()
                    stats["total_chats"] = row["count"]

                # Archived chats
                async with db.execute(
                    "SELECT COUNT(*) as count FROM chats WHERE archived = 1"
                ) as cursor:
                    row = await cursor.fetchone()
                    stats["archived_chats"] = row["count"]

                # Total messages
                async with db.execute(
                    "SELECT COUNT(*) as count FROM messages"
                ) as cursor:
                    row = await cursor.fetchone()
                    stats["total_messages"] = row["count"]

                # Most recent chat
                async with db.execute(
                    """
                    SELECT updated_at FROM chats ORDER BY updated_at DESC LIMIT 1
                """
                ) as cursor:
                    row = await cursor.fetchone()
                    stats["last_activity"] = row["updated_at"] if row else None

                # Most used tags
                async with db.execute(
                    """
                    SELECT tag, COUNT(*) as count
                    FROM chat_tags
                    GROUP BY tag
                    ORDER BY count DESC
                    LIMIT 10
                """
                ) as cursor:
                    rows = await cursor.fetchall()
                    stats["popular_tags"] = [
                        {"tag": row["tag"], "count": row["count"]} for row in rows
                    ]

                return stats

        except Exception as e:
            print(f"Error getting chat stats: {e}")
            return {}

    async def cleanup_old_data(self, days_old: int = 90) -> dict[str, int]:
        """Clean up old archived chats and data"""
        await self.initialize()

        cutoff_date = datetime.now().replace(microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)

        try:
            async with aiosqlite.connect(str(self.db_path)) as db:
                # Count what will be deleted
                async with db.execute(
                    """
                    SELECT COUNT(*) as count FROM chats
                    WHERE archived = 1 AND updated_at < ?
                """,
                    (cutoff_date.isoformat(),),
                ) as cursor:
                    row = await cursor.fetchone()
                    deleted_chats = row["count"]

                # Delete old archived chats
                await db.execute(
                    """
                    DELETE FROM chats
                    WHERE archived = 1 AND updated_at < ?
                """,
                    (cutoff_date.isoformat(),),
                )

                await db.commit()

                return {"deleted_chats": deleted_chats}

        except Exception as e:
            print(f"Error cleaning up old data: {e}")
            return {"deleted_chats": 0}
