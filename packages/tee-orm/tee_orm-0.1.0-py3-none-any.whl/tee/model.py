import json
import re
from typing import Any, Dict, List, Tuple, Type, TypeVar

from .fields import Field  # 确保 Field 类可用

M = TypeVar("M", bound="Model")


class ModelMeta(type):
    def __new__(cls, name: str, bases: Tuple[type, ...], dct: Dict[str, Any]) -> type:
        # 遍历类属性，找到所有字段
        fields: Dict[str, Field] = {}
        for attr_name, attr_value in dct.items():
            if isinstance(attr_value, Field):
                attr_value.name = attr_name  # 将字段名绑定到字段实例
                fields[attr_name] = attr_value

        # 存储字段信息到类中
        dct["_fields"] = fields
        return super().__new__(cls, name, bases, dct)


class Model(metaclass=ModelMeta):
    # 类型注解：告诉类型检查器这个属性存在（由元类设置）
    _fields: Dict[str, Field] = {}

    def __init__(self, **kwargs):
        # 初始化字段值
        self._values: Dict[str, Any] = {}

        # 为每个字段设置默认值
        for field_name, _ in self._fields.items():
            if field_name in kwargs:
                self._values[field_name] = kwargs[field_name]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._values.copy()

    def to_json(self, **kwargs) -> str:
        """转换为JSON字符串"""
        return json.dumps(self._values, **kwargs)

    def __str__(self):
        return f"{self.__class__.__name__}({', '.join(f'{k}={repr(v)}' for k, v in self._values.items())})"

    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        """使对象可迭代，FastAPI可以正确序列化"""
        return iter(self._values.items())

    def dict(self):
        """Pydantic兼容方法"""
        return self._values.copy()

    def __getitem__(self, key):
        """支持字典式访问"""
        return self._values[key]

    def keys(self):
        """返回所有键"""
        return self._values.keys()

    def values(self):
        """返回所有值"""
        return self._values.values()

    def items(self):
        """返回所有键值对"""
        return self._values.items()

    @classmethod
    def get_fields(cls) -> Dict[str, Field]:
        """获取所有字段"""
        return cls._fields

    @classmethod
    def get_field_names(cls) -> List[str]:
        """获取所有字段名"""
        return list(cls._fields.keys())

    @classmethod
    def get_table_name(cls) -> str:
        """获取表名（默认为类名的 snake case）"""
        snake_case = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        return snake_case

    @classmethod
    def select(cls: type[M], fields: List[str] | None = None):
        from .select import Select

        return Select[M](cls, fields)

    @classmethod
    def insert(cls: type[M]):
        from .insert import Insert

        return Insert[M](cls)

    @classmethod
    def update(cls: type[M]):
        from .update import Update

        return Update[M](cls)

    @classmethod
    def delete(cls: type[M]):
        from .delete import Delete

        return Delete[M](cls)
