from typing import Any, TypeVar

from .condition import Condition, ConditionTree
from .operation import Operation

T = TypeVar("T")


class Where:
    def __init__(self, logic="and") -> None:
        self._condition_tree = ConditionTree(logic)

    def tree(self) -> ConditionTree:
        return self._condition_tree

    def eq(self, field: str, value: Any) -> "Where":
        self._condition_tree.add_condition(Condition(field, value))
        return self

    def ne(self, field: str, value: Any) -> "Where":
        self._condition_tree.add_condition(Condition(field, value, Operation.NE))
        return self

    def gt(self, field: str, value: Any) -> "Where":
        self._condition_tree.add_condition(Condition(field, value, Operation.GT))
        return self

    def ge(self, field: str, value: Any) -> "Where":
        self._condition_tree.add_condition(Condition(field, value, Operation.GE))
        return self

    def lt(self, field: str, value: Any) -> "Where":
        self._condition_tree.add_condition(Condition(field, value, Operation.LT))
        return self

    def le(self, field: str, value: Any) -> "Where":
        self._condition_tree.add_condition(Condition(field, value, Operation.LE))
        return self

    def in_(self, field: str, value: Any) -> "Where":
        self._condition_tree.add_condition(Condition(field, value, Operation.IN))
        return self

    def l_like(self, field: str, value: Any) -> "Where":
        self._condition_tree.add_condition(Condition(field, f"%{value}", Operation.LIKE))
        return self

    def r_like(self, field: str, value: Any) -> "Where":
        self._condition_tree.add_condition(Condition(field, f"{value}%", Operation.LIKE))
        return self

    def like(self, field: str, value: Any) -> "Where":
        self._condition_tree.add_condition(Condition(field, f"%{value}%", Operation.LIKE))
        return self

    def or_(self, or_conditions: "Or") -> "Where":
        self._condition_tree.add_tree(or_conditions._condition_tree)
        return self

    def count(self):
        return self._condition_tree.count()


class Or(Where):
    def __init__(self) -> None:
        super().__init__("or")
