from typing import Any, Dict, Generic, List, Literal, Tuple, Type, TypeVar

from .executor import Executor
from .model import Model
from .statement import Statement
from .where import Where

# 将 T 的约束修改为 Model 的子类
M = TypeVar("M", bound=Model)


class Insert(Generic[M]):

    def __init__(self, model: Type[M]):
        self._model = model
        self._where = Where()

    def execute(
        self,
        data: Dict[str, Any] | M,
        duplicate_key_update: List[str] | Literal["all"] | None = None,
    ) -> int:
        fields: List[str] = []
        args: Tuple[Any, ...] = ()
        placeholder: List[str] = []
        field_names = self._model.get_field_names()

        if isinstance(data, Model):
            data = data.to_dict()

        for k, v in data.items():
            if k in field_names:
                fields.append(k)
                args += (v,)
                placeholder.append("%s")

        if len(fields) == 0:
            raise ValueError("no valid field found")

        table_name = self._model.get_table_name()
        sql = f'INSERT INTO {table_name}({",".join(fields)}) VALUES({",".join(placeholder)})'

        if duplicate_key_update is not None:
            if isinstance(duplicate_key_update, str) and duplicate_key_update == "all":
                sql += f' ON DUPLICATE KEY UPDATE {",".join([f"{k}=VALUES({k})" for k in fields])}'
            elif len(duplicate_key_update) > 0:
                sql += f' ON DUPLICATE KEY UPDATE {",".join([f"{k}=VALUES({k})" for k in duplicate_key_update])}'

        stmt = Statement(sql, args)
        return Executor.execute(stmt)

    def execute_bulk(self, data_list: List[Dict[str, Any]]) -> int:
        if len(data_list) == 0:
            return 0

        fields: List[str] = []
        placeholder: List[str] = []
        field_names = self._model.get_field_names()
        for k in data_list[0].keys():
            if k in field_names:
                fields.append(k)
                placeholder.append("%s")

        if len(fields) == 0:
            raise ValueError("no valid field found")

        table_name = self._model.get_table_name()
        sql = f'INSERT INTO {table_name}({",".join(fields)}) VALUES({",".join(placeholder)})'

        args = ()
        for data in data_list:
            arg: Tuple[Any, ...] = ()
            for k in fields:
                arg += (data.get(k),)
            args += (arg,)

        stmt = Statement(sql, args)
        return Executor.execute_many(stmt)
