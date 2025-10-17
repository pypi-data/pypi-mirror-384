from typing import TypeVar

from pyparsing import CaselessKeyword, Group, oneOf, opAssoc
from pyparsing.helpers import infix_notation

from .proto_grammar import ProtoGrammar
from .syntax import ConditionSyntax

TConditionSyntax = TypeVar("TConditionSyntax", bound=ConditionSyntax)


def get_attribute_references(instring):
    """
    Return a list of attribute references in the condition expression.

    attribute_reference ::= relation_name "." attribute_name | attribute_name

    :param instring: a condition expression.
    :return: a list of attribute references.
    """
    parsed = ConditionGrammar().conditions.parseString(instring)
    result = parsed if isinstance(parsed[0], str) else parsed[0]

    attribute_refs = []

    def collect_attributes(item):
        if hasattr(item, "attribute_reference") and item.attribute_reference:
            attribute_refs.extend(item.attribute_reference.asList())
        if hasattr(item, "__iter__") and not isinstance(item, str):
            for subitem in item:
                collect_attributes(subitem)

    collect_attributes(result)
    return attribute_refs


class ConditionGrammar(ProtoGrammar[TConditionSyntax]):
    """
    A grammar for condition expressions.
    """

    def __init__(self, syntax: TConditionSyntax = ConditionSyntax()):
        """
        Initializes a ConditionGrammar. Uses the default syntax if none
        is provided.

        :param syntax: a syntax for this grammar.
        """
        super().__init__(syntax)

    @property
    def comparator_op(self):
        return oneOf(
            [
                self.syntax.equal_op,
                self.syntax.not_equal_op,
                self.syntax.not_equal_alt_op,
                self.syntax.less_than_op,
                self.syntax.less_than_equal_op,
                self.syntax.greater_than_op,
                self.syntax.greater_than_equal_op,
            ]
        )

    @property
    def not_op(self):
        return CaselessKeyword(self.syntax.not_op)

    @property
    def logical_binary_op(self):
        """
        logical_binary_op ::=  and_op | or_op
        """
        return CaselessKeyword(self.syntax.and_op) | CaselessKeyword(self.syntax.or_op)

    @property
    def operand(self):
        """
        operand ::= identifier | string_literal | number
        """
        return (
            self.attribute_reference("attribute_reference*")
            | self.string_literal
            | self.number
        )

    @property
    def condition(self):
        """
        condition ::= operand comparator_op operand | not_op condition |
                  paren_left condition paren_right
        not_op and grouping rules are defined using infixNotation in
        conditions.
        """
        return Group(self.operand + self.comparator_op + self.operand)

    @property
    def conditions(self):
        """
        conditions ::= condition | condition logical_binary_op conditions
        Note: By default lpar and rpar arguments are suppressed.
        """
        return infix_notation(
            base_expr=self.condition,
            op_list=[
                (self.not_op, 1, opAssoc.RIGHT),
                (self.logical_binary_op, 2, opAssoc.RIGHT),
            ],
            lpar=self.syntax.paren_left,
            rpar=self.syntax.paren_right,
        )
