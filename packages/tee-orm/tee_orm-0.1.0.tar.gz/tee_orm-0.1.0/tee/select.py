from typing import Any, Generic, List, Type, TypeVar

from .errors import MultipleRecordsError, NotFoundError
from .executor import Executor
from .fields import Field
from .model import Model
from .statement import Statement
from .where import Where

# 将 T 的约束修改为 Model 的子类
M = TypeVar("M", bound=Model)


class Select(Generic[M]):

    def __init__(self, model: Type[M], fields: List[str] | None = None):
        self._model = model
        self.fields = fields

        if self.fields is None:
            self.fields = model.get_field_names()
        self._where = Where()
        self._order_by: List[str] = []

    def or_(self):
        pass

    def eq(self, field: Field, value: Any) -> "Select[M]":
        self._where.eq(field.name, value)
        return self

    def ne(self, field: Field, value: Any) -> "Select[M]":
        self._where.ne(field.name, value)
        return self

    def gt(self, field: Field, value: Any) -> "Select[M]":
        self._where.gt(field.name, value)
        return self

    def ge(self, field: Field, value: Any) -> "Select[M]":
        self._where.ge(field.name, value)
        return self

    def lt(self, field: Field, value: Any) -> "Select[M]":
        self._where.lt(field.name, value)
        return self

    def le(self, field: Field, value: Any) -> "Select[M]":
        self._where.le(field.name, value)
        return self

    def in_(self, field: Field, value: Any) -> "Select[M]":
        self._where.in_(field.name, value)
        return self

    def l_like(self, field: Field, value: Any) -> "Select[M]":
        self._where.l_like(field.name, value)
        return self

    def r_like(self, field: Field, value: Any) -> "Select[M]":
        self._where.r_like(field.name, value)
        return self

    def like(self, field: Field, value: Any) -> "Select[M]":
        self._where.like(field.name, value)
        return self

    def desc(self, *order_by: Field) -> "Select[M]":
        self._order_by.extend([f"{field.name} desc" for field in order_by])
        return self

    def asc(self, *order_by: Field) -> "Select[M]":
        self._order_by.extend([f"{field.name} asc" for field in order_by])
        return self

    def limit(self, limit: int) -> "Select[M]":
        self._limit = limit
        return self

    def offset(self, offset: int) -> "Select[M]":
        self._offset = offset
        return self

    def one(self) -> M | None:
        try:
            return self.get()
        except NotFoundError:
            return None

    def first(self) -> M | None:
        try:
            return self.get(first=True)
        except NotFoundError:
            return None

    def get(self, first: bool = False) -> M:
        # 构建 SELECT 部分
        fields = ", ".join(self.fields) if self.fields else "*"
        table_name = self._model.get_table_name()
        sql = f"SELECT {fields} FROM {table_name}"
        args = ()

        # 构建 WHERE 部分
        if self._where.count() > 0:
            where_sql, where_args = self._where.tree().parse("%s")
            sql += f" WHERE {where_sql}"
            args += where_args

        # 添加 ORDER BY 部分
        if len(self._order_by) > 0:
            order_by_sql = ", ".join(self._order_by)
            sql += f" ORDER BY {order_by_sql}"

        # 添加 LIMIT 1
        if first:
            sql += " LIMIT 1"

        stmt = Statement(sql=sql, args=args)
        rows = Executor.select(stmt)
        if not rows or len(rows) == 0:
            raise NotFoundError()
        if len(rows) > 1:
            raise MultipleRecordsError()
        row = rows[0]
        return self._model(**row)

    def list(self) -> List[M]:
        """查询所有记录，返回 Statement"""
        # 构建 SELECT 部分
        fields = ", ".join(self.fields) if self.fields else "*"
        table_name = self._model.get_table_name()
        sql = f"SELECT {fields} FROM {table_name}"
        args = ()

        # 构建 WHERE 部分
        if self._where.count() > 0:
            where_sql, where_args = self._where.tree().parse("%s")
            sql += f" WHERE {where_sql}"
            args += where_args

        # 添加 ORDER BY 部分
        if len(self._order_by) > 0:
            order_by_sql = ", ".join(self._order_by)
            sql += f" ORDER BY {order_by_sql}"

        # 添加 LIMIT 和 OFFSET 部分
        if hasattr(self, "_limit"):
            sql += f" LIMIT {self._limit}"
        if hasattr(self, "_offset"):
            sql += f" OFFSET {self._offset}"

        stmt = Statement(sql=sql, args=args)
        rows = Executor.select(stmt)
        return [self._model(**row) for row in rows]
