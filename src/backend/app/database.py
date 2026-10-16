import os
from contextlib import contextmanager

from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor

from app.config import DATABASE_URL

pool = None

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "schema.sql")


def init_pool():
    global pool
    pool = ThreadedConnectionPool(1, 10, DATABASE_URL, cursor_factory=RealDictCursor)

    # schema.sql only uses CREATE ... IF NOT EXISTS, so applying it on every start is safe
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            with open(SCHEMA_PATH, encoding="utf-8") as f:
                cur.execute(f.read())
        conn.commit()
    finally:
        pool.putconn(conn)


def close_pool():
    if pool:
        pool.closeall()


@contextmanager
def db_session():
    """A pooled connection that commits on success and rolls back on error."""
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def get_db():
    """FastAPI dependency: one pooled connection for the length of the request."""
    with db_session() as conn:
        yield conn
