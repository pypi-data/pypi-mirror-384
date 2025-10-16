"""
Work Queue - Manage work items with priorities and persistence
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import aiosqlite
import uuid

logger = logging.getLogger(__name__)


class WorkQueue:
    """Persistent work queue with priority management"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialized = False

    async def initialize(self):
        """Initialize the database and create tables"""
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS work_items (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    priority INTEGER DEFAULT 3,
                    status TEXT DEFAULT 'pending',
                    source TEXT,
                    source_file TEXT,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    attempts INTEGER DEFAULT 0,
                    last_attempt_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    result TEXT,
                    error_message TEXT,
                    total_execution_time REAL DEFAULT 0.0,
                    started_at TIMESTAMP,
                    total_elapsed_time REAL DEFAULT 0.0,
                    commit_sha TEXT
                )
            """
            )

            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_work_items_priority_status 
                ON work_items (priority DESC, status, created_at)
            """
            )

            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_work_items_status 
                ON work_items (status)
            """
            )

            # Migrate existing databases to add timing columns and task types table
            await self._migrate_timing_columns(db)
            await self._migrate_task_types_table(db)

            await db.commit()

        self._initialized = True

    async def _migrate_timing_columns(self, db):
        """Add timing columns to existing databases if they don't exist"""
        try:
            # Check if timing columns exist
            cursor = await db.execute("PRAGMA table_info(work_items)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]

            # Add missing timing columns
            if "total_execution_time" not in column_names:
                await db.execute(
                    "ALTER TABLE work_items ADD COLUMN total_execution_time REAL DEFAULT 0.0"
                )
                logger.info("Added total_execution_time column to existing database")

            if "started_at" not in column_names:
                await db.execute(
                    "ALTER TABLE work_items ADD COLUMN started_at TIMESTAMP"
                )
                logger.info("Added started_at column to existing database")

            if "total_elapsed_time" not in column_names:
                await db.execute(
                    "ALTER TABLE work_items ADD COLUMN total_elapsed_time REAL DEFAULT 0.0"
                )
                logger.info("Added total_elapsed_time column to existing database")

            if "commit_sha" not in column_names:
                await db.execute("ALTER TABLE work_items ADD COLUMN commit_sha TEXT")
                logger.info("Added commit_sha column to existing database")

        except Exception as e:
            logger.warning(f"Migration warning (non-critical): {e}")

    async def _migrate_task_types_table(self, db):
        """Create task_types table and populate with defaults if it doesn't exist"""
        try:
            # Check if task_types table exists
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='task_types'"
            )
            table_exists = await cursor.fetchone()

            if not table_exists:
                # Create task_types table
                await db.execute(
                    """
                    CREATE TABLE task_types (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        agent TEXT,
                        commit_template TEXT,
                        emoji TEXT,
                        file_patterns TEXT,
                        is_default BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Insert default task types
                default_types = [
                    {
                        "id": "bug_fix",
                        "name": "Bug Fix",
                        "description": "Fix existing issues or bugs",
                        "agent": "tech-lead",
                        "commit_template": "fix: {title}",
                        "emoji": "🐛",
                        "file_patterns": '["src/components/buggy_component.py", "tests/test_fix.py"]',
                        "is_default": 1,
                    },
                    {
                        "id": "feature",
                        "name": "Feature",
                        "description": "Add new functionality",
                        "agent": "general-purpose",
                        "commit_template": "feat: {title}",
                        "emoji": "✨",
                        "file_patterns": '["src/features/new_feature.py", "src/api/feature_endpoint.py"]',
                        "is_default": 1,
                    },
                    {
                        "id": "test",
                        "name": "Test",
                        "description": "Add or update tests",
                        "agent": "general-purpose",
                        "commit_template": "test: {title}",
                        "emoji": "🧪",
                        "file_patterns": '["tests/test_*.py", "spec/*.spec.js"]',
                        "is_default": 1,
                    },
                    {
                        "id": "refactor",
                        "name": "Refactor",
                        "description": "Code refactoring without changing functionality",
                        "agent": "code-reviewer",
                        "commit_template": "refactor: {title}",
                        "emoji": "♻️",
                        "file_patterns": '["src/legacy_code.py", "src/improved_code.py"]',
                        "is_default": 1,
                    },
                    {
                        "id": "documentation",
                        "name": "Documentation",
                        "description": "Documentation updates and improvements",
                        "agent": "general-purpose",
                        "commit_template": "docs: {title}",
                        "emoji": "📝",
                        "file_patterns": '["README.md", "docs/api_documentation.md"]',
                        "is_default": 1,
                    },
                ]

                for task_type in default_types:
                    await db.execute(
                        """
                        INSERT INTO task_types
                        (id, name, description, agent, commit_template, emoji, file_patterns, is_default)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            task_type["id"],
                            task_type["name"],
                            task_type["description"],
                            task_type["agent"],
                            task_type["commit_template"],
                            task_type["emoji"],
                            task_type["file_patterns"],
                            task_type["is_default"],
                        ),
                    )

                logger.info("Created task_types table and populated with default types")

        except Exception as e:
            logger.error(f"Error migrating task_types table: {e}")
            # Continue without task_types table

        logger.debug(f"✅ Work queue initialized: {self.db_path}")

    async def close(self):
        """Close the work queue (for testing)"""
        # SQLite connections are closed automatically, but this method
        # provides a consistent interface for tests
        pass

    async def work_exists(
        self, source_file: str, exclude_statuses: List[str] = None
    ) -> bool:
        """Check if work item with given source_file already exists"""
        if exclude_statuses is None:
            exclude_statuses = ["failed"]  # Don't prevent retrying failed items

        async with aiosqlite.connect(self.db_path) as db:
            query = "SELECT COUNT(*) FROM work_items WHERE source_file = ?"
            params = [source_file]

            if exclude_statuses:
                placeholders = ",".join("?" * len(exclude_statuses))
                query += f" AND status NOT IN ({placeholders})"
                params.extend(exclude_statuses)

            cursor = await db.execute(query, params)
            count = (await cursor.fetchone())[0]
            return count > 0

    async def add_work(self, work_item: Dict[str, Any]) -> str:
        """Add a new work item to the queue"""
        work_id = str(uuid.uuid4())

        # Set defaults
        work_item.setdefault("status", "pending")
        work_item.setdefault("priority", 3)
        work_item.setdefault("attempts", 0)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO work_items 
                (id, type, title, description, priority, status, source, source_file, context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    work_id,
                    work_item["type"],
                    work_item["title"],
                    work_item.get("description", ""),
                    work_item["priority"],
                    work_item["status"],
                    work_item.get("source", ""),
                    work_item.get("source_file", ""),
                    json.dumps(work_item.get("context", {})),
                ),
            )
            await db.commit()

        logger.debug(
            f"➕ Added work item: {work_item['title']} (priority: {work_item['priority']})"
        )
        return work_id

    async def get_next_work(self) -> Optional[Dict[str, Any]]:
        """Get the highest priority pending work item"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Get highest priority pending work item (exclude hold status)
            cursor = await db.execute(
                """
                SELECT * FROM work_items
                WHERE status = 'pending'
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            """
            )

            row = await cursor.fetchone()

            if not row:
                return None

            work_item = dict(row)

            # Parse JSON context
            if work_item["context"]:
                try:
                    work_item["context"] = json.loads(work_item["context"])
                except json.JSONDecodeError:
                    work_item["context"] = {}
            else:
                work_item["context"] = {}

            # Mark as active and increment attempts
            await db.execute(
                """
                UPDATE work_items 
                SET status = 'active', 
                    attempts = attempts + 1,
                    last_attempt_at = CURRENT_TIMESTAMP,
                    started_at = CASE WHEN started_at IS NULL THEN CURRENT_TIMESTAMP ELSE started_at END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (work_item["id"],),
            )

            await db.commit()

            work_item["attempts"] += 1
            work_item["status"] = "active"
            logger.debug(
                f"📋 Retrieved work item: {work_item['title']} (attempt #{work_item['attempts']})"
            )

            return work_item

    async def complete_work(self, work_id: str, result: Dict[str, Any]):
        """Mark a work item as completed with results and timing"""
        async with aiosqlite.connect(self.db_path) as db:
            # Extract execution time from result
            execution_time = 0.0
            try:
                if isinstance(result, dict):
                    # Try various ways to extract execution time
                    execution_time = (
                        result.get("execution_time", 0)
                        or result.get("result", {}).get("execution_time", 0)
                        or 0.0
                    )
            except (TypeError, AttributeError):
                execution_time = 0.0

            await db.execute(
                """
                UPDATE work_items 
                SET status = 'completed',
                    result = ?,
                    completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP,
                    total_execution_time = total_execution_time + ?,
                    total_elapsed_time = (
                        CASE 
                            WHEN started_at IS NOT NULL 
                            THEN (julianday(CURRENT_TIMESTAMP) - julianday(started_at)) * 86400.0
                            ELSE (julianday(CURRENT_TIMESTAMP) - julianday(created_at)) * 86400.0
                        END
                    )
                WHERE id = ?
            """,
                (json.dumps(result), execution_time, work_id),
            )

            await db.commit()

        logger.debug(
            f"✅ Completed work item: {work_id} (+{execution_time:.1f}s execution)"
        )

    async def fail_work(
        self,
        work_id: str,
        error_message: str,
        max_retries: int = 3,
        execution_time: float = 0.0,
    ):
        """Mark a work item as failed, or retry if under retry limit"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get current attempts
            cursor = await db.execute(
                """
                SELECT attempts, title FROM work_items WHERE id = ?
            """,
                (work_id,),
            )

            row = await cursor.fetchone()
            if not row:
                logger.error(f"Work item not found: {work_id}")
                return

            attempts, title = row

            if attempts >= max_retries:
                # Final failure - record total elapsed time
                await db.execute(
                    """
                    UPDATE work_items 
                    SET status = 'failed',
                        error_message = ?,
                        updated_at = CURRENT_TIMESTAMP,
                        total_execution_time = total_execution_time + ?,
                        total_elapsed_time = (
                            CASE 
                                WHEN started_at IS NOT NULL 
                                THEN (julianday(CURRENT_TIMESTAMP) - julianday(started_at)) * 86400.0
                                ELSE (julianday(CURRENT_TIMESTAMP) - julianday(created_at)) * 86400.0
                            END
                        )
                    WHERE id = ?
                """,
                    (error_message, execution_time, work_id),
                )

                logger.error(
                    f"❌ Work item failed permanently: {title} (after {attempts} attempts, +{execution_time:.1f}s)"
                )
            else:
                # Retry later - accumulate execution time but don't calculate elapsed time yet
                await db.execute(
                    """
                    UPDATE work_items 
                    SET status = 'pending',
                        error_message = ?,
                        updated_at = CURRENT_TIMESTAMP,
                        total_execution_time = total_execution_time + ?
                    WHERE id = ?
                """,
                    (error_message, execution_time, work_id),
                )

                logger.warning(
                    f"⚠️ Work item will be retried: {title} (attempt {attempts}/{max_retries}, +{execution_time:.1f}s)"
                )

            await db.commit()

    async def get_work_item(self, work_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific work item by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                """
                SELECT * FROM work_items WHERE id = ?
            """,
                (work_id,),
            )

            row = await cursor.fetchone()

            if not row:
                return None

            work_item = dict(row)

            # Parse JSON fields
            for field in ["context", "result"]:
                if work_item[field]:
                    try:
                        work_item[field] = json.loads(work_item[field])
                    except json.JSONDecodeError:
                        work_item[field] = {}
                else:
                    work_item[field] = {}

            return work_item

    async def get_recent_work(
        self, limit: int = 10, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent work items, optionally filtered by status"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            query = "SELECT * FROM work_items"
            params = []

            if status:
                query += " WHERE status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()

            work_items = []
            for row in rows:
                work_item = dict(row)

                # Parse JSON fields
                for field in ["context", "result"]:
                    if work_item[field]:
                        try:
                            work_item[field] = json.loads(work_item[field])
                        except json.JSONDecodeError:
                            work_item[field] = {}
                    else:
                        work_item[field] = {}

                work_items.append(work_item)

            return work_items

    async def get_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}

            # Count by status
            cursor = await db.execute(
                """
                SELECT status, COUNT(*) as count 
                FROM work_items 
                GROUP BY status
            """
            )

            rows = await cursor.fetchall()
            for row in rows:
                stats[row[0]] = row[1]

            # Set defaults for missing statuses
            for status in ["pending", "hold", "active", "completed", "failed"]:
                stats.setdefault(status, 0)

            # Total items
            stats["total"] = sum(stats.values())

            # Recent activity (last 24 hours)
            cursor = await db.execute(
                """
                SELECT COUNT(*) FROM work_items 
                WHERE created_at > datetime('now', '-1 day')
            """
            )
            stats["recent_24h"] = (await cursor.fetchone())[0]

            return stats

    async def cleanup_old_items(self, days_old: int = 30):
        """Clean up old completed/failed items"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                DELETE FROM work_items 
                WHERE status IN ('completed', 'failed') 
                AND created_at < datetime('now', '-{} days')
            """.format(
                    days_old
                )
            )

            deleted_count = cursor.rowcount
            await db.commit()

            if deleted_count > 0:
                logger.info(f"🗑️ Cleaned up {deleted_count} old work items")

            return deleted_count

    async def get_work_by_id(self, work_id: str) -> Optional[Dict[str, Any]]:
        """Get specific work item by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT id, type, title, description, priority, status, source, 
                       context, created_at, updated_at, attempts, last_attempt_at, 
                       completed_at, result, total_execution_time, started_at, 
                       total_elapsed_time, commit_sha
                FROM work_items 
                WHERE id = ?
            """,
                (work_id,),
            ) as cursor:
                row = await cursor.fetchone()

                if row:
                    return {
                        "id": row[0],
                        "type": row[1],
                        "title": row[2],
                        "description": row[3],
                        "priority": row[4],
                        "status": row[5],
                        "source": row[6],
                        "context": json.loads(row[7]) if row[7] else {},
                        "created_at": row[8],
                        "updated_at": row[9],
                        "attempts": row[10],
                        "last_attempt_at": row[11],
                        "completed_at": row[12],
                        "result": json.loads(row[13]) if row[13] else None,
                        "total_execution_time": row[14],
                        "started_at": row[15],
                        "total_elapsed_time": row[16],
                        "commit_sha": row[17],
                    }
                return None

    async def remove_work(self, work_id: str) -> bool:
        """Remove work item by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM work_items WHERE id = ?", (work_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def update_work(self, work_id: str, updates: Dict[str, Any]) -> bool:
        """Update work item by ID"""
        if not updates:
            return False

        # Build dynamic UPDATE query
        set_clauses = []
        values = []

        for key, value in updates.items():
            if key == "context":
                set_clauses.append(f"{key} = ?")
                values.append(json.dumps(value))
            else:
                set_clauses.append(f"{key} = ?")
                values.append(value)

        values.append(work_id)  # FOR WHERE clause

        query = f"UPDATE work_items SET {', '.join(set_clauses)} WHERE id = ?"

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, values)
            await db.commit()
            return cursor.rowcount > 0

    async def update_commit_sha(self, work_id: str, commit_sha: str) -> bool:
        """Update the commit SHA for a work item"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                UPDATE work_items
                SET commit_sha = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (commit_sha, work_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def hold_work(self, work_id: str, reason: str = None) -> bool:
        """Put a work item on hold"""
        updates = {"status": "hold", "updated_at": "CURRENT_TIMESTAMP"}
        if reason:
            # Store hold reason in context
            work_item = await self.get_work_item(work_id)
            if work_item:
                context = work_item.get("context", {})
                context["hold_reason"] = reason
                context["held_at"] = datetime.now().isoformat()
                updates["context"] = context

        success = await self.update_work(work_id, updates)
        if success:
            logger.info(f"⏸️ Work item put on hold: {work_id}")
        return success

    async def release_work(self, work_id: str) -> bool:
        """Release a work item from hold to pending status"""
        work_item = await self.get_work_item(work_id)
        if not work_item:
            return False

        if work_item["status"] != "hold":
            logger.warning(
                f"Work item {work_id} is not on hold (status: {work_item['status']})"
            )
            return False

        # Clear hold-related context data
        context = work_item.get("context", {})
        context.pop("hold_reason", None)
        context.pop("held_at", None)
        context["released_at"] = datetime.now().isoformat()

        updates = {
            "status": "pending",
            "context": context,
            "updated_at": "CURRENT_TIMESTAMP",
        }

        success = await self.update_work(work_id, updates)
        if success:
            logger.info(f"▶️ Work item released from hold: {work_id}")
        return success

    async def health_check(self) -> dict:
        """Return health status of the work queue"""
        stats = await self.get_stats()

        return {
            "initialized": self._initialized,
            "database_path": self.db_path,
            "total_tasks": stats.get("total", 0),
            "status": "healthy",
        }

    async def get_pending_work(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pending work items ordered by priority"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                """
                SELECT * FROM work_items 
                WHERE status = 'pending'
                ORDER BY priority DESC, created_at ASC 
                LIMIT ?
                """,
                (limit,),
            )
            rows = await cursor.fetchall()

            work_items = []
            for row in rows:
                work_item = dict(row)
                # Parse JSON fields
                for field in ["context", "result"]:
                    if work_item[field]:
                        try:
                            work_item[field] = json.loads(work_item[field])
                        except json.JSONDecodeError:
                            work_item[field] = {}
                    else:
                        work_item[field] = {}
                work_items.append(work_item)

            return work_items

    async def mark_work_active(self, work_id: str):
        """Mark a work item as active"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE work_items 
                SET status = 'active', 
                    attempts = attempts + 1,
                    last_attempt_at = CURRENT_TIMESTAMP,
                    started_at = CASE WHEN started_at IS NULL THEN CURRENT_TIMESTAMP ELSE started_at END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (work_id,),
            )
            await db.commit()

    async def mark_work_completed(self, work_id: str, result: Dict[str, Any]):
        """Mark a work item as completed"""
        await self.complete_work(work_id, result)

    async def mark_work_failed(
        self, work_id: str, error_info: Dict[str, Any], max_retries: int = 3
    ):
        """Mark a work item as failed"""
        error_message = error_info.get("error", "Unknown error")
        if "details" in error_info:
            error_message += f": {error_info['details']}"
        await self.fail_work(work_id, error_message, max_retries)
