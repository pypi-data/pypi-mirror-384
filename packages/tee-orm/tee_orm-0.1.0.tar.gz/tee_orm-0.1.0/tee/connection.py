import threading
from contextlib import contextmanager

import pymysql
from pymysql.connections import Connection

from .database import get_db

thread_local = threading.local()


class ConnectionContext:
    """连接上下文,用于跟踪连接状态"""

    def __init__(self, connection: Connection, in_transaction: bool = False):
        self.connection = connection
        self.in_transaction = in_transaction


def new_connection(db_name: str = "default", autocommit: bool = True):
    db = get_db(db_name)
    connection = pymysql.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        password=db.password,
        database=db.database,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=autocommit,
        ssl=db.ssl,
    )
    return connection


def get_connection(db_name: str = "default"):
    """获取当前线程的连接,如果在事务中则返回事务连接"""
    # 优先返回事务连接
    if hasattr(thread_local, "transaction_context") and thread_local.transaction_context is not None:
        return thread_local.transaction_context.connection

    # 否则返回或创建普通连接
    if not hasattr(thread_local, "connection_context") or thread_local.connection_context is None:
        db = get_db(db_name)
        connection = pymysql.connect(
            host=db.host,
            port=db.port,
            user=db.user,
            password=db.password,
            database=db.database,
            cursorclass=pymysql.cursors.DictCursor,
        )
        thread_local.connection_context = ConnectionContext(connection, in_transaction=False)
    return thread_local.connection_context.connection


def close_connection():
    """关闭普通连接(不会关闭事务连接)"""
    if hasattr(thread_local, "connection_context") and thread_local.connection_context is not None:
        if not thread_local.connection_context.in_transaction:
            thread_local.connection_context.connection.close()
            thread_local.connection_context = None


def is_in_transaction() -> bool:
    """检查当前线程是否在事务中"""
    return hasattr(thread_local, "transaction_context") and thread_local.transaction_context is not None


@contextmanager
def transaction(db_name: str = "default"):
    """
    事务管理上下文管理器

    使用示例:
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name) VALUES (%s)", ("Alice",))
            cursor.execute("UPDATE accounts SET balance = balance - 100 WHERE user_id = 1")
    """
    conn = new_connection(db_name, autocommit=False)
    old_transaction_context = getattr(thread_local, "transaction_context", None)
    thread_local.transaction_context = ConnectionContext(conn, in_transaction=True)

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
        thread_local.transaction_context = old_transaction_context
