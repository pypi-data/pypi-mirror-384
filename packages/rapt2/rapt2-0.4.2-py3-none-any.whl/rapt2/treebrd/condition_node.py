from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto

from .grammars.condition_grammar import ConditionGrammar
from .grammars.syntax import Syntax


class UnaryConditionalOperator(Enum):
    NOT = auto()
    DEFINED = auto()

    @classmethod
    def from_syntax(cls, syntax: Syntax, instring: str) -> "UnaryConditionalOperator":
        match instring:
            case syntax.not_op:
                return cls.NOT
            case syntax.defined_op:
                return cls.DEFINED
            case _:
                raise ValueError


class BinaryConditionalOperator(Enum):
    AND = auto()
    OR = auto()
    EQUAL = auto()
    NOT_EQUAL = auto()
    LESS_THAN = auto()
    LESS_THAN_EQUAL = auto()
    GREATER_THAN = auto()
    GREATER_THAN_EQUAL = auto()

    @classmethod
    def from_syntax(cls, syntax: Syntax, instring: str) -> "BinaryConditionalOperator":
        match instring:
            case syntax.and_op:
                return cls.AND
            case syntax.or_op:
                return cls.OR
            case syntax.equal_op:
                return cls.EQUAL
            case syntax.not_equal_op | syntax.not_equal_alt_op:
                return cls.NOT_EQUAL
            case syntax.less_than_op:
                return cls.LESS_THAN
            case syntax.less_than_equal_op:
                return cls.LESS_THAN_EQUAL
            case syntax.greater_than_op:
                return cls.GREATER_THAN
            case syntax.greater_than_equal_op:
                return cls.GREATER_THAN_EQUAL
            case _:
                raise ValueError


@dataclass(frozen=True)
class ConditionNode(ABC):
    @abstractmethod
    def attribute_references(self) -> list[str]:
        """
        Return a list of attribute references in this condition node.
        """
        raise NotImplementedError()


@dataclass(frozen=True)
class IdentityConditionNode(ConditionNode):
    ident: str

    def attribute_references(self) -> list[str]:
        try:
            ConditionGrammar().attribute_reference.parse_string(self.ident)
            return [self.ident]
        except Exception:
            return []


@dataclass(frozen=True)
class UnaryConditionNode(ConditionNode):
    op: UnaryConditionalOperator
    child: ConditionNode

    def attribute_references(self) -> list[str]:
        return self.child.attribute_references()


@dataclass(frozen=True)
class BinaryConditionNode(ConditionNode):
    op: BinaryConditionalOperator
    left: ConditionNode
    right: ConditionNode

    def attribute_references(self) -> list[str]:
        return list(
            self.left.attribute_references() + self.right.attribute_references()
        )
