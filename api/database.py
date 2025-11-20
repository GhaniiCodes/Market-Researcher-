import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from contextlib import contextmanager

# Database file path
DB_PATH = Path(__file__).parent / "query_history.db"

def _parse_timestamp(timestamp_str: str) -> datetime:
    """Convert SQLite timestamp string to datetime object"""
    if isinstance(timestamp_str, datetime):
        return timestamp_str
    # SQLite timestamps are in format: YYYY-MM-DD HH:MM:SS
    try:
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        # Try ISO format as fallback
        try:
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return datetime.now()

def _row_to_dict(row) -> dict:
    """Convert SQLite row to dict with proper timestamp conversion"""
    row_dict = dict(row)
    if "timestamp" in row_dict and row_dict["timestamp"]:
        row_dict["timestamp"] = _parse_timestamp(row_dict["timestamp"])
    return row_dict

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Initialize the database with required tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                query_id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                agent TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                execution_time REAL NOT NULL
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON query_history(timestamp DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent 
            ON query_history(agent)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_query_search 
            ON query_history(query)
        """)
        
        conn.commit()

def save_query(query: str, agent: str, response: str, execution_time: float) -> int:
    """Save a query to the database"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO query_history (query, agent, response, execution_time)
            VALUES (?, ?, ?, ?)
        """, (query, agent, response, execution_time))
        return cursor.lastrowid

def get_query_by_id(query_id: int) -> Optional[dict]:
    """Retrieve a specific query by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT query_id, query, agent, response, timestamp, execution_time
            FROM query_history
            WHERE query_id = ?
        """, (query_id,))
        row = cursor.fetchone()
        if row:
            return _row_to_dict(row)
        return None

def get_query_history(
    limit: int = 50,
    offset: int = 0,
    agent_filter: Optional[str] = None,
    search: Optional[str] = None
) -> tuple[List[dict], int]:
    """Retrieve query history with filtering and pagination"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Build query with filters
        where_clauses = []
        params = []
        
        if agent_filter:
            where_clauses.append("agent = ?")
            params.append(agent_filter)
        
        if search:
            where_clauses.append("query LIKE ?")
            params.append(f"%{search}%")
        
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Get total count
        cursor.execute(f"""
            SELECT COUNT(*) as total
            FROM query_history
            {where_sql}
        """, params)
        total = cursor.fetchone()["total"]
        
        # Get paginated results
        cursor.execute(f"""
            SELECT query_id, query, agent, response, timestamp, execution_time
            FROM query_history
            {where_sql}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset])
        
        rows = cursor.fetchall()
        items = [_row_to_dict(row) for row in rows]
        
        return items, total

def get_statistics() -> dict:
    """Get query statistics"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Total queries
        cursor.execute("SELECT COUNT(*) as total FROM query_history")
        total = cursor.fetchone()["total"]
        
        # Queries by agent
        cursor.execute("""
            SELECT agent, COUNT(*) as count
            FROM query_history
            GROUP BY agent
        """)
        queries_by_agent = {row["agent"]: row["count"] for row in cursor.fetchall()}
        
        # Average execution time
        cursor.execute("""
            SELECT AVG(execution_time) as avg_time
            FROM query_history
        """)
        avg_time = cursor.fetchone()["avg_time"] or 0.0
        
        # Last query time
        cursor.execute("""
            SELECT timestamp
            FROM query_history
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        last_row = cursor.fetchone()
        if last_row and last_row["timestamp"]:
            last_query_time = _parse_timestamp(last_row["timestamp"])
        else:
            last_query_time = None
        
        return {
            "total_queries": total,
            "queries_by_agent": queries_by_agent,
            "avg_execution_time": round(avg_time, 3),
            "last_query_time": last_query_time
        }

def delete_query(query_id: int) -> bool:
    """Delete a specific query"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM query_history WHERE query_id = ?", (query_id,))
        return cursor.rowcount > 0

def clear_history() -> int:
    """Clear all query history"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM query_history")
        return cursor.rowcount