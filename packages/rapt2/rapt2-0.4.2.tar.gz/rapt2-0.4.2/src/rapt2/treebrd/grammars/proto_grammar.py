from typing import Generic, TypeVar

from pyparsing import (Combine, Optional, ParserElement, Regex, Word,
                       alphanums, alphas, pyparsing_common, quotedString,
                       removeQuotes)

from .syntax import BaseSyntax

ParserElement.enablePackrat()

TSyntax = TypeVar("TSyntax", bound=BaseSyntax)


class ProtoGrammar(Generic[TSyntax]):
    """
    A grammar with fundamental rules for characters, strings, and
    numbers.

    The rules are annotated with their BNF equivalents. For a complete
    specification refer to the associated grammar file.
    """

    syntax: TSyntax

    def __init__(self, syntax: TSyntax = BaseSyntax()):
        """
        Initializes a ProtoGrammar. Uses the default syntax if none
        is provided.

        :param syntax: a syntax for this grammar.
        """
        self.syntax = syntax

    def parse(self, instring):
        """
        Defined by descendants.
        :param instring: A string to parse.
        """
        raise NotImplementedError

    @property
    def character(self):
        """
        character ::= letter | digit | "_"
        """
        return alphanums + "_"

    @property
    def number(self):
        """
        number ::= float | integer | natural_number
        """
        return Regex(r"[-+]?[0-9]*\.?[0-9]+")

    @property
    def string_literal(self):
        """
        string_literal ::= "'" string "'" | "\"" string "\""

        Any successful match is converted to a single quoted string to simplify
        post-parsed operations.
        """
        return quotedString.setParseAction(
            lambda s, loc, t: "'{string}'".format(string=removeQuotes(s, loc, t))
        )

    @property
    def identifier(self):
        """
        identifier ::= letter | letter string
        """
        return Word(alphas, self.character).setParseAction(
            pyparsing_common.downcaseTokens
        )

    @property
    def relation_name(self):
        """
        relation_name ::= identifier
        """
        return self.identifier

    @property
    def attribute_name(self):
        """
        attribute_name ::= identifier
        """
        return self.identifier

    @property
    def attribute_reference(self):
        """
        attribute_reference ::= relation_name "." attribute_name |
        attribute_name
        """
        return Combine((Optional(self.relation_name + ".") + self.attribute_name))
