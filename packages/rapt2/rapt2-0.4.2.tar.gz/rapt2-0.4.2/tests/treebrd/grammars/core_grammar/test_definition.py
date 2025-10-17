import unittest

from pyparsing import ParseException

from rapt2.treebrd.grammars.core_grammar import CoreGrammar


class TestDefinition(unittest.TestCase):
    def setUp(self):
        self.parser = CoreGrammar()

    def test_definition_single_attribute(self):
        expression = "R(a);"
        expected = [["r", ["a"]]]
        actual = self.parser.statements.parseString(expression).asList()
        self.assertEqual(expected, actual)

    def test_definition_multiple_attributes(self):
        expression = "R(a, b, c);"
        expected = [["r", ["a", "b", "c"]]]
        actual = self.parser.statements.parseString(expression).asList()
        self.assertEqual(expected, actual)

    def test_definition_two_attributes(self):
        expression = "R(a, b);"
        expected = [["r", ["a", "b"]]]
        actual = self.parser.statements.parseString(expression).asList()
        self.assertEqual(expected, actual)

    def test_definition_with_spacing(self):
        expression = "R ( a , b , c ) ;"
        expected = [["r", ["a", "b", "c"]]]
        actual = self.parser.statements.parseString(expression).asList()
        self.assertEqual(expected, actual)

    def test_definition_relation_name_only(self):
        # Test that definition requires attributes
        expression = "R();"
        self.assertRaises(
            ParseException, self.parser.statements.parseString, expression
        )

    def test_definition_no_attributes(self):
        # Test that definition requires at least one attribute
        # R; parses as a relation expression, not a definition
        expression = "R;"
        expected = [["r"]]
        actual = self.parser.statements.parseString(expression).asList()
        self.assertEqual(expected, actual)

    def test_definition_without_terminator(self):
        # Test that definition without terminator fails in statement context
        expression = "R(a, b, c)"
        self.assertRaises(
            ParseException, self.parser.statements.parseString, expression
        )

    def test_definition_parsing_only(self):
        # Test that definition parsing works without terminator
        expression = "R(a, b, c)"
        expected = [["r", ["a", "b", "c"]]]
        actual = self.parser.definition.parseString(expression, parseAll=True).asList()
        self.assertEqual(expected, actual)

    def test_multiple_definitions(self):
        expression = "R1(a, b); R2(c, d); R3(e);"
        expected = [
            ["r1", ["a", "b"]],
            ["r2", ["c", "d"]],
            ["r3", ["e"]],
        ]
        actual = self.parser.statements.parseString(expression).asList()
        self.assertEqual(expected, actual)

    def test_definition_mixed_with_assignments(self):
        expression = "R1(a, b); R2 := R1; R3(c, d);"
        expected = [
            ["r1", ["a", "b"]],
            [["r2"], ":=", ["r1"]],
            ["r3", ["c", "d"]],
        ]
        actual = self.parser.statements.parseString(expression).asList()
        self.assertEqual(expected, actual)

    # Exception tests

    def test_definition_missing_left_paren(self):
        expression = "R a, b, c);"
        self.assertRaises(
            ParseException, self.parser.statements.parseString, expression
        )

    def test_definition_missing_right_paren(self):
        expression = "R(a, b, c;"
        self.assertRaises(
            ParseException, self.parser.statements.parseString, expression
        )

    def test_definition_empty_attributes(self):
        expression = "R();"
        self.assertRaises(
            ParseException, self.parser.statements.parseString, expression
        )

    def test_definition_trailing_comma(self):
        expression = "R(a, b, c,);"
        self.assertRaises(
            ParseException, self.parser.statements.parseString, expression
        )

    def test_definition_leading_comma(self):
        expression = "R(, a, b, c);"
        self.assertRaises(
            ParseException, self.parser.statements.parseString, expression
        )

    def test_definition_double_comma(self):
        expression = "R(a, , b, c);"
        self.assertRaises(
            ParseException, self.parser.statements.parseString, expression
        )