from typing import Any, Optional, Type, Union, overload


class Field:
    def __init__(self, type: str):
        self.name: str = ""  # 字段名，稍后由元类设置
        self._type = type


class Str(Field):
    def __init__(self):
        super().__init__("str")

    @overload
    def __get__(self, instance: None, owner: Optional[Type] = None) -> "Str": ...

    @overload
    def __get__(self, instance: object, owner: Optional[Type] = None) -> Optional[str]: ...

    def __get__(self, instance: Any, owner: Optional[Type] = None) -> Union["Str", Optional[str]]:
        """描述符协议：获取字段值"""
        if instance is None:
            return self
        if not hasattr(instance, "_values"):
            return None
        value: Optional[str] = instance._values.get(self.name, None)
        return value

    def __set__(self, instance: Any, value: Optional[str]) -> None:
        """描述符协议：设置字段值"""
        if instance is None:
            raise ValueError("Instance cannot be None when setting a value.")
        if not hasattr(instance, "_values"):
            instance._values = {}
        instance._values[self.name] = value


class Int(Field):
    def __init__(self):
        super().__init__("int")

    @overload
    def __get__(self, instance: None, owner: Optional[Type] = None) -> "Int": ...

    @overload
    def __get__(self, instance: object, owner: Optional[Type] = None) -> Optional[int]: ...

    def __get__(self, instance: Any, owner: Optional[Type] = None) -> Union["Int", Optional[int]]:
        """描述符协议：获取字段值"""
        if instance is None:
            return self
        if not hasattr(instance, "_values"):
            return None
        value: Optional[int] = instance._values.get(self.name, None)
        return value

    def __set__(self, instance: Any, value: Optional[int]) -> None:
        """描述符协议：设置字段值"""
        if instance is None:
            raise ValueError("Instance cannot be None when setting a value.")
        if not hasattr(instance, "_values"):
            instance._values = {}
        instance._values[self.name] = value


class Float(Field):
    def __init__(self):
        super().__init__("float")

    @overload
    def __get__(self, instance: None, owner: Optional[Type] = None) -> "Float": ...

    @overload
    def __get__(self, instance: object, owner: Optional[Type] = None) -> Optional[float]: ...

    def __get__(self, instance: Any, owner: Optional[Type] = None) -> Union["Float", Optional[float]]:
        """描述符协议：获取字段值"""
        if instance is None:
            return self
        if not hasattr(instance, "_values"):
            return None
        value: Optional[float] = instance._values.get(self.name, None)
        return value

    def __set__(self, instance: Any, value: Optional[float]) -> None:
        """描述符协议：设置字段值"""
        if instance is None:
            raise ValueError("Instance cannot be None when setting a value.")
        if not hasattr(instance, "_values"):
            instance._values = {}
        instance._values[self.name] = float(value) if value is not None else None


class DateTime(Field):  # 假设 DateTime 存储为字符串
    def __init__(self):
        super().__init__("datetime")

    @overload
    def __get__(self, instance: None, owner: Optional[Type] = None) -> "DateTime": ...

    @overload
    def __get__(self, instance: object, owner: Optional[Type] = None) -> Optional[str]: ...

    def __get__(self, instance: Any, owner: Optional[Type] = None) -> Union["DateTime", Optional[str]]:
        """描述符协议：获取字段值"""
        if instance is None:
            return self
        if not hasattr(instance, "_values"):
            return None
        value: Optional[str] = instance._values.get(self.name, None)
        return value

    def __set__(self, instance: Any, value: Optional[str]) -> None:
        """描述符协议：设置字段值"""
        if instance is None:
            raise ValueError("Instance cannot be None when setting a value.")
        if not hasattr(instance, "_values"):
            instance._values = {}
        instance._values[self.name] = value
