import psycopg2
from config import DB_DSN

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS players (
    id       SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS game_sessions (
    id            SERIAL PRIMARY KEY,
    player_id     INTEGER REFERENCES players(id),
    score         INTEGER   NOT NULL,
    level_reached INTEGER   NOT NULL,
    played_at     TIMESTAMP DEFAULT NOW()
);
"""


def _connect():
    """Return a new psycopg2 connection (raises on failure)."""
    return psycopg2.connect(DB_DSN)


def init_db():
    """Create tables if they don't exist yet."""
    try:
        conn = _connect()
        with conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] init_db error: {e}")
        return False



def get_or_create_player(username: str) -> int | None:
    """
    Return the player's id, creating the row if needed.
    Returns None on DB error.
    """
    try:
        conn = _connect()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO players (username) VALUES (%s) "
                    "ON CONFLICT (username) DO NOTHING",
                    (username,)
                )
                cur.execute(
                    "SELECT id FROM players WHERE username = %s",
                    (username,)
                )
                row = cur.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"[DB] get_or_create_player error: {e}")
        return None



def save_session(player_id: int, score: int, level_reached: int) -> bool:
    """Persist one game session. Returns True on success."""
    try:
        conn = _connect()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO game_sessions (player_id, score, level_reached) "
                    "VALUES (%s, %s, %s)",
                    (player_id, score, level_reached)
                )
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] save_session error: {e}")
        return False


def get_personal_best(player_id: int) -> int:
    """Return the player's all-time best score (0 if none)."""
    try:
        conn = _connect()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(score), 0) FROM game_sessions "
                "WHERE player_id = %s",
                (player_id,)
            )
            row = cur.fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception as e:
        print(f"[DB] get_personal_best error: {e}")
        return 0


def get_leaderboard(limit: int = 10) -> list[dict]:
    """
    Return the top `limit` sessions ordered by score desc.
    Each row: {rank, username, score, level_reached, played_at}
    """
    try:
        conn = _connect()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.username,
                       gs.score,
                       gs.level_reached,
                       gs.played_at
                FROM game_sessions gs
                JOIN players p ON p.id = gs.player_id
                ORDER BY gs.score DESC
                LIMIT %s
                """,
                (limit,)
            )
            rows = cur.fetchall()
        conn.close()
        result = []
        for rank, row in enumerate(rows, start=1):
            result.append({
                "rank":          rank,
                "username":      row[0],
                "score":         row[1],
                "level_reached": row[2],
                "played_at":     row[3].strftime("%Y-%m-%d") if row[3] else "—",
            })
        return result
    except Exception as e:
        print(f"[DB] get_leaderboard error: {e}")
        return []
