from typing import TypeVar

from pyparsing import Group, Literal, OneOrMore, Suppress

from .extended_grammar import ExtendedGrammar
from .syntax import DependencySyntax

TDependencySyntax = TypeVar("TDependencySyntax", bound=DependencySyntax)


class DependencyGrammar(ExtendedGrammar[TDependencySyntax]):
    """
    A parser that recognizes database dependency grammar rules.

    The rules are annotated with their BNF equivalents. For a complete
    specification refer to the associated grammar file.
    """

    syntax: TDependencySyntax

    def __init__(self, syntax: TDependencySyntax = DependencySyntax()):
        """
        Initializes a DependencyGrammar. Uses the default syntax if none
        is provided.

        :param syntax: a syntax for this grammar.
        """
        super().__init__(syntax)

    def parse(self, instring):
        instring = r"" + instring
        return self.statements.parseString(instring, parseAll=True)

    @property
    def pk(self):
        """
        pk ::= "pk"
        """
        return Literal(self.syntax.pk_op)

    @property
    def pk_dep(self):
        """
        pk_dep ::= pk param_start attribute_list param_stop relation_name
        """
        return Group(self.pk + self.parameter(self.attribute_list) + self.relation_name)

    @property
    def mvd(self):
        """
        mvd ::= "mvd"
        """
        return Literal(self.syntax.mvd_op)

    @property
    def select_or_relation(self):
        """
        select_or_relation ::= (select param_start conditions param_stop relation_name) | relation_name
        """
        return (
            (
                Literal(self.syntax.select_op)
                + self.parameter(self.conditions)
                + self.relation_name
            )
            | self.relation_name
        )

    @property
    def cond_dep_expr(self):
        """
        cond_dep_expr ::= param_start attribute_name delim attribute_name param_stop select_or_relation
        """
        return self.parameter(
            self.attribute_name + Suppress(self.syntax.delim) + self.attribute_name
        ) + self.select_or_relation

    @property
    def mvd_dep(self):
        """
        mvd_dep ::= mvd cond_dep_expr
        """
        return Group(self.mvd + self.cond_dep_expr)

    @property
    def fd(self):
        """
        fd ::= "fd"
        """
        return Literal(self.syntax.fd_op)

    @property
    def fd_dep(self):
        """
        fd_dep ::= fd cond_dep_expr
        """
        return Group(self.fd + self.cond_dep_expr)

    @property
    def inc_eq(self):
        """
        inc_eq ::= "inc="
        """
        return Literal(self.syntax.inc_equiv_op)

    @property
    def inc_expr(self):
        """
        inc_expr ::= param_start attribute_name delim attribute_name param_stop paren_left select_or_relation delim select_or_relation paren_right
        """
        return self.parameter(
            self.attribute_name + Suppress(self.syntax.delim) + self.attribute_name
        ) + self.parenthesize(
            Group(self.select_or_relation) + Suppress(self.syntax.delim) + Group(self.select_or_relation)
        )

    @property
    def inc_eq_dep(self):
        """
        inc_eq_dep ::= inc_eq inc_expr
        """
        return Group(self.inc_eq + self.inc_expr)

    @property
    def inc_subs(self):
        """
        inc_subs ::= "inc⊆"
        """
        return Literal(self.syntax.inc_subset_op)

    @property
    def inc_subs_dep(self):
        """
        inc_subs_dep ::= inc_subs inc_expr
        """
        return Group(self.inc_subs + self.inc_expr)

    @property
    def dep(self):
        """
        dep ::= pk_dep | mvd_dep | fd_dep | inc_eq_dep | inc_subs_dep
        """
        return (
            self.pk_dep
            | self.mvd_dep
            | self.fd_dep
            | self.inc_eq_dep
            | self.inc_subs_dep
        )

    @property
    def dep_statement(self):
        """
        dep_statement ::= dep terminate
        """
        return self.dep + Suppress(self.syntax.terminator)

    @property
    def statement(self):
        """
        statement ::= dep_statement | statement
        """
        return self.dep_statement | super().statement

    @property
    def statements(self):
        """
        An ordered collection of dependency and relational algebra statements.
        """
        return OneOrMore(self.statement)
