from typing import Any, Dict, Generic, Type, TypeVar

from .executor import Executor
from .model import Field, Model
from .statement import Statement
from .where import Where

# 将 T 的约束修改为 Model 的子类
M = TypeVar("M", bound=Model)


class Update(Generic[M]):

    def __init__(self, model: Type[M]):
        self._model = model
        self._where = Where()
        self._update_fields: Dict[str, Any] = {}

    def or_(self):
        pass

    def eq(self, field: Field, value: Any) -> "Update[M]":
        self._where.eq(field.name, value)
        return self

    def ne(self, field: Field, value: Any) -> "Update[M]":
        self._where.ne(field.name, value)
        return self

    def gt(self, field: Field, value: Any) -> "Update[M]":
        self._where.gt(field.name, value)
        return self

    def ge(self, field: Field, value: Any) -> "Update[M]":
        self._where.ge(field.name, value)
        return self

    def lt(self, field: Field, value: Any) -> "Update[M]":
        self._where.lt(field.name, value)
        return self

    def le(self, field: Field, value: Any) -> "Update[M]":
        self._where.le(field.name, value)
        return self

    def in_(self, field: Field, value: Any) -> "Update[M]":
        self._where.in_(field.name, value)
        return self

    def l_like(self, field: Field, value: Any) -> "Update[M]":
        self._where.l_like(field.name, value)
        return self

    def r_like(self, field: Field, value: Any) -> "Update[M]":
        self._where.r_like(field.name, value)
        return self

    def like(self, field: Field, value: Any) -> "Update[M]":
        self._where.like(field.name, value)
        return self

    def set(self, args: Dict[str, Any] | None = None, **kwargs: Any) -> "Update[M]":
        if args is None:
            args = {}

        args.update(kwargs)

        valid_fields: Dict[str, Any] = {}
        for k, v in args.items():
            if k in self._model.get_field_names():
                valid_fields[k] = v

        if len(valid_fields) == 0:
            raise ValueError("valid fields is required")

        self._update_fields = valid_fields
        return self

    def execute(self) -> int:
        table_name = self._model.get_table_name()
        sql = f'UPDATE {table_name} SET {",".join([f"{k}=?" for k in self._update_fields.keys()])}'
        args = tuple(self._update_fields.values())

        # 构建 WHERE 部分
        if self._where.count() > 0:
            where_sql, where_args = self._where.tree().parse("%s")
            sql += f" WHERE {where_sql}"
            args += where_args
        else:
            raise ValueError("Update operation requires at least one condition to prevent full table deletion.")

        stmt = Statement(sql, where_args)
        return Executor.execute(stmt)
