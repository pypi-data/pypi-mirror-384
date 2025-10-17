from typing import TypeVar

from pyparsing import CaselessKeyword, Group, Literal, infixNotation, opAssoc

from .core_grammar import CoreGrammar
from .syntax import ExtendedSyntax

TExtendedSyntax = TypeVar("TExtendedSyntax", bound=ExtendedSyntax)


class ExtendedGrammar(CoreGrammar[TExtendedSyntax]):
    """
    A parser that recognizes an extended relational algebra grammar.

    The rules are annotated with their BNF equivalents. For a complete
    specification refer to the associated grammar file.
    """

    syntax: TExtendedSyntax

    def __init__(self, syntax: TExtendedSyntax = ExtendedSyntax()):
        """
        Initializes an ExtendedGrammar. Uses the default syntax if none
        is provided.

        :param syntax: a syntax for this grammar.
        """
        super().__init__(syntax)

    @property
    def natural_join(self):
        """
        natural_join_expr ::= expression natural_join expression
        """
        return CaselessKeyword(self.syntax.natural_join_op)

    @property
    def theta_join(self):
        """
        select_expr ::= select param_start conditions param_stop expression
        """
        long = self.parametrize(self.syntax.theta_join_op, self.conditions)
        short = self.parametrize(self.syntax.join_op, self.conditions).setParseAction(
            self.theta_parse_action
        )
        return long ^ short

    def theta_parse_action(self, s, loc, t):
        t[0] = self.syntax.theta_join_op
        return t

    @property
    def full_outer_join(self):
        """
        full_outer_join_expr ::= expression \\full_outer_join param_start conditions param_stop expression
        """
        return self.parametrize(self.syntax.full_outer_join_op, self.conditions)

    @property
    def left_outer_join(self):
        """
        left_outer_join_expr ::= expression \\left_outer_join param_start conditions param_stop expression
        """
        return self.parametrize(self.syntax.left_outer_join_op, self.conditions)

    @property
    def right_outer_join(self):
        """
        right_outer_join_expr ::= expression \\right_outer_join param_start conditions param_stop expression
        """
        return self.parametrize(self.syntax.right_outer_join_op, self.conditions)

    @property
    def binary_op_p1(self):
        return (
            super().binary_op_p1
            ^ self.natural_join
            ^ self.theta_join
            ^ self.full_outer_join
            ^ self.left_outer_join
            ^ self.right_outer_join
        )

    @property
    def intersect(self):
        """
        intersect_op ::= intersect_name
        """
        return CaselessKeyword(self.syntax.intersect_op)

    @property
    def defined_op(self):
        return CaselessKeyword(self.syntax.defined_op)

    @property
    def defined_condition(self):
        """
        defined_condition ::= defined_op "(" operand ")"
        """
        return Group(
            self.defined_op
            + Literal(self.syntax.paren_left).suppress()
            + self.operand
            + Literal(self.syntax.paren_right).suppress()
        )

    @property
    def condition(self):
        """
        condition ::= condition | defined_condition
        """
        return super().condition | self.defined_condition

    @property
    def expression(self):
        return infixNotation(
            self.relation,
            [
                (self.unary_op, 1, opAssoc.RIGHT),
                (self.binary_op_p1, 2, opAssoc.LEFT),
                (self.intersect, 2, opAssoc.LEFT),
                (self.binary_op_p2, 2, opAssoc.LEFT),
            ],
            lpar=self.syntax.paren_left,
            rpar=self.syntax.paren_right,
        )

    def is_unary(self, operator):
        return operator in {
            self.syntax.select_op,
            self.syntax.project_op,
            self.syntax.rename_op,
        }

    def is_binary(self, operator):
        return operator in {
            self.syntax.intersect_op,
            self.syntax.natural_join_op,
            self.syntax.theta_join_op,
            self.syntax.full_outer_join_op,
            self.syntax.left_outer_join_op,
            self.syntax.right_outer_join_op,
        } or super().is_binary(operator)
