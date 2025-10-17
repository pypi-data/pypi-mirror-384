import unittest

from pyparsing import ParseException

from rapt2.treebrd.grammars.condition_grammar import (ConditionGrammar,
                                                      get_attribute_references)
from tests.treebrd.grammars.grammar_test_case import GrammarTestCase


class TestConditionRules(GrammarTestCase):
    def setUp(self):
        self.parser = ConditionGrammar()

    def test_comparator(self):
        parse = self.parse_function(self.parser.comparator_op)

        self.assertEqual(parse("="), ["="])
        self.assertEqual(parse("!="), ["!="])
        self.assertEqual(parse("<>"), ["<>"])
        self.assertEqual(parse("<"), ["<"])
        self.assertEqual(parse("<="), ["<="])
        self.assertEqual(parse(">"), [">"])
        self.assertEqual(parse(">="), [">="])

    def test_comparator_exp(self):
        parse = self.parse_function(self.parser.comparator_op)

        self.assertRaises(ParseException, parse, "==")
        self.assertRaises(ParseException, parse, "><")
        self.assertRaises(ParseException, parse, "=<")
        self.assertRaises(ParseException, parse, "=>")

    def test_logical_unary(self):
        parse = self.parse_function(self.parser.not_op)

        self.assertEqual(parse("not"), ["not"])
        self.assertEqual(parse("NOT"), ["not"])

    def test_logical_binary(self):
        parse = self.parse_function(self.parser.logical_binary_op)

        self.assertEqual(parse("and"), ["and"])
        self.assertEqual(parse("AND"), ["and"])
        self.assertEqual(parse("or"), ["or"])
        self.assertEqual(parse("OR"), ["or"])

    def test_operand(self):
        parse = self.parse_function(self.parser.operand)

        self.assertEqual(parse('"Secret to life"'), ["'Secret to life'"])
        self.assertEqual(parse("is__"), ["is__"])
        self.assertEqual(parse("1.3337"), ["1.3337"])

    def test_operand_exp(self):
        parse = self.parse_function(self.parser.operand)

        self.assertRaises(ParseException, parse, "=")
        self.assertRaises(ParseException, parse, "Need space!")

    def test_condition(self):
        parse = self.parse_function(self.parser.condition)

        self.assertEqual(parse("2 > 7"), [["2", ">", "7"]])
        self.assertEqual(parse("secret = 3"), [["secret", "=", "3"]])
        self.assertEqual(parse('"name" != "mane"'), [["'name'", "!=", "'mane'"]])

    def test_condition_exp_fragments(self):
        parse = self.parse_function(self.parser.condition)

        self.assertRaises(ParseException, parse, "'Happiness' =")
        self.assertRaises(ParseException, parse, "< you")
        self.assertRaises(ParseException, parse, "<>")

    # Testing a single condition

    def test_conditions_single(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [["2", ">", "7"]]
        actual = parse("2 > 7")
        self.assertEqual(actual, expected)

    def test_conditions_par(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [["2", ">", "7"]]
        actual = parse("(2 > 7)")
        self.assertEqual(actual, expected)

    def test_conditions_not(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [["not", ["2", ">", "7"]]]
        actual = parse("not (2 > 7)")
        self.assertEqual(actual, expected)

    def test_conditions_and(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [[["2", ">", "7"], "and", ["3", "<>", "3"]]]
        actual = parse("2 > 7 and 3 <> 3")
        self.assertEqual(actual, expected)

    def test_conditions_and_par(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [[["2", ">", "7"], "and", ["3", "<>", "3"]]]
        actual = parse("(2 > 7) and (3 <> 3)")
        self.assertEqual(actual, expected)

    def test_conditions_or(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [[["2", ">", "7"], "or", ["3", "<>", "3"]]]
        actual = parse("(2 > 7) or (3 <> 3)")
        self.assertEqual(actual, expected)

    def test_conditions_unary_binary_simple(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [[["not", ["2", ">", "7"]], "and", ["3", "<>", "3"]]]
        actual = parse("not 2 > 7 and 3 <> 3")
        self.assertEqual(actual, expected)

    def test_conditions_unary_binary_simple_forced(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [["not", [["2", ">", "7"], "and", ["3", "<>", "3"]]]]
        actual = parse("not (2 > 7 and 3 <> 3)")
        self.assertEqual(actual, expected)

    def test_conditions_binary_unary_simple(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [[["3", "<>", "3"], "or", ["not", ["2", ">", "7"]]]]
        actual = parse("3 <> 3 or not 2 > 7")
        self.assertEqual(expected, actual)

    def test_conditions_chained_and_two(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [[["1", "=", "1"], "and", ["2", "=", "2"]]]
        actual = parse("1 = 1 and 2 = 2")
        self.assertEqual(actual, expected)

    def test_conditions_chained_and_three(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [[["1", "=", "1"], "and", [["2", "=", "2"], "and", ["3", "=", "3"]]]]
        actual = parse("1 = 1 and 2 = 2 and 3 = 3")
        self.assertEqual(actual, expected)

    def test_conditions_chained_and_four(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [
            [
                ["1", "=", "1"],
                "and",
                [["2", "=", "2"], "and", [["3", "=", "3"], "and", ["4", "=", "4"]]],
            ]
        ]
        actual = parse("1 = 1 and 2 = 2 and 3 = 3 and 4 = 4")
        self.assertEqual(actual, expected)

    def test_conditions_chained_or_two(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [[["1", "=", "1"], "or", ["2", "=", "2"]]]
        actual = parse("1 = 1 or 2 = 2")
        self.assertEqual(actual, expected)

    def test_conditions_chained_or_three(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [[["1", "=", "1"], "or", [["2", "=", "2"], "or", ["3", "=", "3"]]]]
        actual = parse("1 = 1 or 2 = 2 or 3 = 3")
        self.assertEqual(actual, expected)

    def test_conditions_chained_or_four(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [
            [
                ["1", "=", "1"],
                "or",
                [["2", "=", "2"], "or", [["3", "=", "3"], "or", ["4", "=", "4"]]],
            ]
        ]
        actual = parse("1 = 1 or 2 = 2 or 3 = 3 or 4 = 4")
        self.assertEqual(actual, expected)

    def test_conditions_mixed_chained_and_or(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [
            [
                ["1", "=", "1"],
                "and",
                [["2", "=", "2"], "or", [["3", "=", "3"], "and", ["4", "=", "4"]]],
            ]
        ]
        actual = parse("1 = 1 and 2 = 2 or 3 = 3 and 4 = 4")
        self.assertEqual(actual, expected)

    def test_conditions_mixed_chained_or_and(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [
            [
                ["1", "=", "1"],
                "or",
                [["2", "=", "2"], "and", [["3", "=", "3"], "or", ["4", "=", "4"]]],
            ]
        ]
        actual = parse("1 = 1 or 2 = 2 and 3 = 3 or 4 = 4")
        self.assertEqual(actual, expected)

    def test_conditions_chained_with_parentheses_and(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [[["1", "=", "1"], "and", [["2", "=", "2"], "and", ["3", "=", "3"]]]]
        actual = parse("1 = 1 and (2 = 2 and 3 = 3)")
        self.assertEqual(actual, expected)

    def test_conditions_chained_with_parentheses_or(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [[["1", "=", "1"], "or", [["2", "=", "2"], "or", ["3", "=", "3"]]]]
        actual = parse("1 = 1 or (2 = 2 or 3 = 3)")
        self.assertEqual(actual, expected)

    def test_conditions_chained_with_not_and(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [[["not", ["1", "=", "1"]], "and", ["not", ["2", "=", "2"]]]]
        actual = parse("not 1 = 1 and not 2 = 2")
        self.assertEqual(actual, expected)

    def test_conditions_chained_with_not_or(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [[["not", ["1", "=", "1"]], "or", ["not", ["2", "=", "2"]]]]
        actual = parse("not 1 = 1 or not 2 = 2")
        self.assertEqual(actual, expected)

    def test_conditions_chained_with_not_mixed(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [
            [
                ["not", ["1", "=", "1"]],
                "and",
                [
                    ["2", "=", "2"],
                    "or",
                    [["3", "=", "3"], "and", ["not", ["4", "=", "4"]]],
                ],
            ]
        ]
        actual = parse("not 1 = 1 and 2 = 2 or 3 = 3 and not 4 = 4")
        self.assertEqual(actual, expected)

    def test_conditions_chained_with_not_parentheses(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [
            [
                "not",
                [
                    ["1", "=", "1"],
                    "and",
                    [["2", "=", "2"], "or", [["3", "=", "3"], "and", ["4", "=", "4"]]],
                ],
            ]
        ]
        actual = parse("not (1 = 1 and 2 = 2 or 3 = 3 and 4 = 4)")
        self.assertEqual(actual, expected)

    def test_conditions_chained_complex_nested(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [
            [
                [["1", "=", "1"], "and", [["2", "=", "2"], "or", ["3", "=", "3"]]],
                "and",
                [["4", "=", "4"], "or", [["5", "=", "5"], "and", ["6", "=", "6"]]],
            ]
        ]
        actual = parse("(1 = 1 and (2 = 2 or 3 = 3)) and (4 = 4 or (5 = 5 and 6 = 6))")
        self.assertEqual(actual, expected)

    def test_conditions_chained_with_strings(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [
            [
                ["'name'", "=", "'john'"],
                "and",
                [
                    ["'age'", ">", "18"],
                    "or",
                    [["'status'", "=", "'active'"], "and", ["'role'", "!=", "'admin'"]],
                ],
            ]
        ]
        actual = parse(
            "'name' = 'john' and 'age' > 18 or 'status' = 'active' and 'role' != 'admin'"
        )
        self.assertEqual(actual, expected)

    def test_conditions_chained_with_numbers(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [
            [
                ["1.5", ">", "1.0"],
                "and",
                [
                    ["2.7", "<", "3.0"],
                    "or",
                    [["4.2", ">=", "4.0"], "and", ["5.1", "<=", "6.0"]],
                ],
            ]
        ]
        actual = parse("1.5 > 1.0 and 2.7 < 3.0 or 4.2 >= 4.0 and 5.1 <= 6.0")
        self.assertEqual(actual, expected)

    def test_conditions_chained_with_identifiers(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [
            [
                ["x", "=", "y"],
                "and",
                [["a", "!=", "b"], "or", [["c", "<", "d"], "and", ["e", ">=", "f"]]],
            ]
        ]
        actual = parse("x = y and a != b or c < d and e >= f")
        self.assertEqual(actual, expected)


class TestConditionAttrs(unittest.TestCase):
    def test_conditions_binary_unary(self):
        expected = ["answer"]
        self.assertEqual(expected, get_attribute_references("answer=42"))

    def test_conditions_binary_unary_with_prefix(self):
        expected = ["a.answer"]
        self.assertEqual(expected, get_attribute_references("a.answer=42"))

    def test_conditions_binary_unary_reversed(self):
        expected = ["answer"]
        self.assertEqual(expected, get_attribute_references("42=answer"))

    def test_conditions_binary_unary_no_attr(self):
        self.assertEqual([], get_attribute_references("42=42"))

    def test_conditions_binary_unary_two_attrs(self):
        expected = ["answer", "known"]
        self.assertEqual(expected, get_attribute_references("answer=known"))

    def test_conditions_binary_two_attrs(self):
        expected = ["answer", "known"]
        self.assertEqual(expected, get_attribute_references("answer=known and 42=42"))

    def test_conditions_binary_man_attrs(self):
        expected = ["answer", "known", "answer", "unknown"]
        self.assertEqual(
            expected, get_attribute_references("answer=known and answer=unknown")
        )
