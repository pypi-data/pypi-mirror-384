from typing import Any, Tuple


class Statement:
    def __init__(self, sql: str, args: Tuple[Any, ...] = ()):
        self.sql = sql  # SQL 语句模板
        self.args = args  # 参数列表

    def get_sql(self) -> str:
        return self.sql

    def get_args(self) -> Tuple[Any, ...]:
        return self.args
