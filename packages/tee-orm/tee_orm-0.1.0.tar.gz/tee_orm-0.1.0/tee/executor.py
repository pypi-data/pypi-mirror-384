import logging
from typing import Any, Dict, Tuple

from pymysql.cursors import DictCursor

from .connection import close_connection, get_connection
from .statement import Statement


class Executor:

    @staticmethod
    def select(stmt: Statement, db_name: str = "default") -> Tuple[Dict[str, Any], ...]:
        """执行查询语句，返回结果元组"""
        try:
            conn = get_connection(db_name=db_name)
            # logging.debug(f"Executing SQL: {sql}, Args: {args}")
            cursor: DictCursor = conn.cursor(DictCursor)
            sql = stmt.get_sql()
            args = stmt.get_args()
            logging.debug(f"Executing SQL: {sql}, Args: {args}")
            cursor.execute(sql, args)
            results = cursor.fetchall()
            cursor.close()
        finally:
            close_connection()
        return results

    @staticmethod
    def execute(stmt: Statement, db_name: str = "default") -> int:
        """执行更新语句，返回受影响的行数"""
        try:
            conn = get_connection(db_name=db_name)
            cursor: DictCursor = conn.cursor(DictCursor)
            sql = stmt.get_sql()
            args = stmt.get_args()
            logging.debug(f"Executing SQL: {sql}, Args: {args}")
            affected = cursor.execute(sql, args)
            cursor.close()
            return affected
        finally:
            close_connection()

    @staticmethod
    def execute_many(stmt: Statement, db_name: str = "default") -> int:
        """执行批量更新或插入语句，返回受影响的行数"""
        try:
            conn = get_connection(db_name=db_name)
            cursor: DictCursor = conn.cursor(DictCursor)
            sql = stmt.get_sql()
            args = stmt.get_args()
            logging.debug(f"Executing SQL: {sql}, Args: {args}")
            affected = cursor.executemany(sql, args)
            cursor.close()
            return affected or 0
        finally:
            close_connection()

    @staticmethod
    def insert(stmt: Statement, db_name: str = "default") -> int:
        """执行 INSERT 语句，返回新增记录的自增主键 ID"""
        try:
            conn = get_connection(db_name=db_name)
            cursor: DictCursor = conn.cursor(DictCursor)
            sql = stmt.get_sql()
            args = stmt.get_args()
            logging.debug(f"Executing SQL: {sql}, Args: {args}")
            cursor.execute(sql, args)
            last_id = cursor.lastrowid  # 获取最后插入的 ID
            cursor.close()
            return last_id
        finally:
            close_connection()
