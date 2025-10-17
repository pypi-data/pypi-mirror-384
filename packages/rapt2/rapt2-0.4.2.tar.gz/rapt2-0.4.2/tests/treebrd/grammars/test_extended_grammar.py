from pyparsing import ParseException

from rapt2.treebrd.grammars.extended_grammar import ExtendedGrammar
from tests.treebrd.grammars.grammar_test_case import GrammarTestCase


class TestIntersect(GrammarTestCase):
    def setUp(self):
        self.parser = ExtendedGrammar()
        self.parse = self.parse_function(self.parser.statements)

    def test_simple(self):
        expression = "zeppelin \\intersect floyd;"
        expected = [[["zeppelin"], "\\intersect", ["floyd"]]]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_multiple(self):
        expression = "zeppelin \\intersect floyd \\intersect doors;"
        expected = [[["zeppelin"], "\\intersect", ["floyd"], "\\intersect", ["doors"]]]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_intersect_precedence_when_before_set_operator(self):
        expression = "zeppelin \\intersect floyd \\union doors;"
        expected = [[[["zeppelin"], "\\intersect", ["floyd"]], "\\union", ["doors"]]]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_intersect_precedence_when_after_set_operator(self):
        expression = "zeppelin \\union floyd \\intersect doors;"
        expected = [[["zeppelin"], "\\union", [["floyd"], "\\intersect", ["doors"]]]]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_other_join(self):
        expression = "zeppelin \\intersect floyd \\join doors;"
        expected = [[["zeppelin"], "\\intersect", [["floyd"], "\\join", ["doors"]]]]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_other_unary(self):
        expression = "\\project_{albums} zeppelin \\intersect \\project_{albums} floyd;"
        expected = [
            [
                ["\\project", ["albums"], ["zeppelin"]],
                "\\intersect",
                ["\\project", ["albums"], ["floyd"]],
            ]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    # Exceptions

    def test_exp_no_relations(self):
        expression = "\\intersect;"
        self.assertRaises(ParseException, self.parse, expression)

    def test_exp_left_relation(self):
        expression = "roger \\intersect;"
        self.assertRaises(ParseException, self.parse, expression)

    def test_exp_right_relation(self):
        expression = "\\intersect waters;"
        self.assertRaises(ParseException, self.parse, expression)


class TestNaturalJoin(GrammarTestCase):
    def setUp(self):
        self.parser = ExtendedGrammar()
        self.parse = self.parse_function(self.parser.statements)

    def test_simple(self):
        expression = "zeppelin \\natural_join floyd;"
        expected = [[["zeppelin"], "\\natural_join", ["floyd"]]]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_multiple(self):
        expression = "zeppelin \\natural_join floyd \\natural_join doors;"
        expected = [
            [["zeppelin"], "\\natural_join", ["floyd"], "\\natural_join", ["doors"]]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_same_precedence(self):
        expression = "zeppelin \\natural_join floyd \\join doors;"
        expected = [[["zeppelin"], "\\natural_join", ["floyd"], "\\join", ["doors"]]]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_other_precedence(self):
        expression = "zeppelin \\union floyd \\natural_join doors;"
        expected = [[["zeppelin"], "\\union", [["floyd"], "\\natural_join", ["doors"]]]]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_other_unary(self):
        expression = (
            "\\project_{albums} zeppelin \\natural_join \\project_{albums} floyd;"
        )
        expected = [
            [
                ["\\project", ["albums"], ["zeppelin"]],
                "\\natural_join",
                ["\\project", ["albums"], ["floyd"]],
            ]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    # Exceptions

    def test_exp_no_relations(self):
        expression = "\\natural_join;"
        self.assertRaises(ParseException, self.parse, expression)

    def test_exp_left_relation(self):
        expression = "roger \\natural_join;"
        self.assertRaises(ParseException, self.parse, expression)

    def test_exp_right_relation(self):
        expression = "\\natural_join waters;"
        self.assertRaises(ParseException, self.parse, expression)


class TestThetaJoin(GrammarTestCase):
    def setUp(self):
        self.parser = ExtendedGrammar()
        self.parse = self.parse_function(self.parser.statements)

    def test_simple(self):
        expression = "zeppelin \\join_{year < 1975} floyd;"
        expected = [[["zeppelin"], "\\theta_join", [["year", "<", "1975"]], ["floyd"]]]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_multiple(self):
        expression = "zeppelin \\join_{year < 1975} floyd \\join_{year < 1960} doors;"
        expected = [
            [
                ["zeppelin"],
                "\\theta_join",
                [["year", "<", "1975"]],
                ["floyd"],
                "\\theta_join",
                [["year", "<", "1960"]],
                ["doors"],
            ]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_same_precedence(self):
        expression = "zeppelin \\join_{year < 1975} floyd \\join doors;"
        expected = [
            [
                ["zeppelin"],
                "\\theta_join",
                [["year", "<", "1975"]],
                ["floyd"],
                "\\join",
                ["doors"],
            ]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_other_precedence(self):
        expression = "zeppelin \\union floyd \\join_{year < 1975} doors;"
        expected = [
            [
                ["zeppelin"],
                "\\union",
                [["floyd"], "\\theta_join", [["year", "<", "1975"]], ["doors"]],
            ]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_other_unary(self):
        expression = (
            "\\project_{albums} zeppelin \\join_{year < 1975} \\project_{albums} floyd;"
        )
        expected = [
            [
                ["\\project", ["albums"], ["zeppelin"]],
                "\\theta_join",
                [["year", "<", "1975"]],
                ["\\project", ["albums"], ["floyd"]],
            ]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    # Exceptions

    def test_exp_basic(self):
        expression = "\\join_;"
        self.assertRaises(ParseException, self.parse, expression)

    def test_exp_no_relation_right(self):
        expression = "zeppelin \\join_{age < 42};"
        self.assertRaises(ParseException, self.parse, expression)

    def test_exp_no_relation_left(self):
        expression = "\\join_{age < 42} floyd;"
        self.assertRaises(ParseException, self.parse, expression)

    def test_exp_empty_attribute_list(self):
        expression = "zeppelin \\join_{} floyd;"
        self.assertRaises(ParseException, self.parse, expression)

    def test_exp_space_before_attributes(self):
        expression = "zeppelin \\join _{age < 42} floyd;"
        self.assertRaises(ParseException, self.parse, expression)


class TestThreeValuedLogic(GrammarTestCase):
    def setUp(self):
        self.parser = ExtendedGrammar()

    def test_defined_op(self):
        parse = self.parse_function(self.parser.defined_op)
        self.assertEqual(parse("defined"), ["defined"])
        self.assertEqual(parse("DEFINED"), ["defined"])

    def test_defined_condition(self):
        parse = self.parse_function(self.parser.defined_condition)
        self.assertEqual(parse("defined( apple )"), [["defined", "apple"]])

    def test_defined_condition_fragments(self):
        parse = self.parse_function(self.parser.defined_condition)
        self.assertRaises(ParseException, parse, "defined (")
        self.assertRaises(ParseException, parse, "defined ( )")

    def test_conditions_single_defined(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [["defined", "apple"]]
        actual = parse("defined(apple)")
        self.assertEqual(actual, expected)

    def test_conditions_defined_with_parentheses(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [["defined", "apple"]]
        actual = parse("(defined(apple))")
        self.assertEqual(actual, expected)

    def test_conditions_not_defined(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [["not", ["defined", "apple"]]]
        actual = parse("not defined(apple)")
        self.assertEqual(actual, expected)

    def test_conditions_defined_and_defined(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [[["defined", "apple"], "and", ["defined", "pear"]]]
        actual = parse("defined(apple) and defined(pear)")
        self.assertEqual(actual, expected)

    def test_conditions_defined_and_defined_with_parentheses(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [[["defined", "apple"], "and", ["defined", "pear"]]]
        actual = parse("(defined(apple)) and (defined(pear))")
        self.assertEqual(actual, expected)

    def test_conditions_defined_or_defined(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [[["defined", "apple"], "or", ["defined", "pear"]]]
        actual = parse("(defined(apple)) or (defined(pear))")
        self.assertEqual(actual, expected)

    def test_conditions_unary_binary_defined_simple(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [[["not", ["defined", "apple"]], "and", ["defined", "pear"]]]
        actual = parse("not defined(apple) and defined(pear)")
        self.assertEqual(actual, expected)

    def test_conditions_unary_binary_defined_forced(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [["not", [["defined", "apple"], "and", ["defined", "pear"]]]]
        actual = parse("not (defined(apple) and defined(pear))")
        self.assertEqual(actual, expected)

    def test_conditions_binary_unary_defined_simple(self):
        parse = self.parse_function(self.parser.conditions)
        expected = [[["defined", "pear"], "or", ["not", ["defined", "apple"]]]]
        actual = parse("defined(pear) or not defined(apple)")
        self.assertEqual(expected, actual)


class TestFullOuterJoin(GrammarTestCase):
    def setUp(self):
        self.parser = ExtendedGrammar()
        self.parse = self.parse_function(self.parser.statements)

    def test_simple(self):
        expression = "zeppelin \\full_outer_join_{year = year} floyd;"
        expected = [
            [["zeppelin"], "\\full_outer_join", [["year", "=", "year"]], ["floyd"]]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_multiple(self):
        expression = "zeppelin \\full_outer_join_{year = year} floyd \\full_outer_join_{year = year} doors;"
        expected = [
            [
                ["zeppelin"],
                "\\full_outer_join",
                [["year", "=", "year"]],
                ["floyd"],
                "\\full_outer_join",
                [["year", "=", "year"]],
                ["doors"],
            ]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_same_precedence(self):
        expression = "zeppelin \\full_outer_join_{year = year} floyd \\join doors;"
        expected = [
            [
                ["zeppelin"],
                "\\full_outer_join",
                [["year", "=", "year"]],
                ["floyd"],
                "\\join",
                ["doors"],
            ]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_other_precedence(self):
        expression = "zeppelin \\union floyd \\full_outer_join_{year = year} doors;"
        expected = [
            [
                ["zeppelin"],
                "\\union",
                [["floyd"], "\\full_outer_join", [["year", "=", "year"]], ["doors"]],
            ]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_other_unary(self):
        expression = "\\project_{albums} zeppelin \\full_outer_join_{year = year} \\project_{albums} floyd;"
        expected = [
            [
                ["\\project", ["albums"], ["zeppelin"]],
                "\\full_outer_join",
                [["year", "=", "year"]],
                ["\\project", ["albums"], ["floyd"]],
            ]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    # Exceptions

    def test_exp_no_relations(self):
        expression = "\\full_outer_join_;"
        self.assertRaises(ParseException, self.parse, expression)

    def test_exp_left_relation(self):
        expression = "roger \\full_outer_join_{year = year};"
        self.assertRaises(ParseException, self.parse, expression)

    def test_exp_right_relation(self):
        expression = "\\full_outer_join_{year = year} floyd;"
        self.assertRaises(ParseException, self.parse, expression)

    def test_exp_empty_conditions(self):
        expression = "zeppelin \\full_outer_join_{} floyd;"
        self.assertRaises(ParseException, self.parse, expression)


class TestLeftOuterJoin(GrammarTestCase):
    def setUp(self):
        self.parser = ExtendedGrammar()
        self.parse = self.parse_function(self.parser.statements)

    def test_simple(self):
        expression = "zeppelin \\left_outer_join_{year = year} floyd;"
        expected = [
            [["zeppelin"], "\\left_outer_join", [["year", "=", "year"]], ["floyd"]]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_multiple(self):
        expression = "zeppelin \\left_outer_join_{year = year} floyd \\left_outer_join_{year = year} doors;"
        expected = [
            [
                ["zeppelin"],
                "\\left_outer_join",
                [["year", "=", "year"]],
                ["floyd"],
                "\\left_outer_join",
                [["year", "=", "year"]],
                ["doors"],
            ]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_same_precedence(self):
        expression = "zeppelin \\left_outer_join_{year = year} floyd \\join doors;"
        expected = [
            [
                ["zeppelin"],
                "\\left_outer_join",
                [["year", "=", "year"]],
                ["floyd"],
                "\\join",
                ["doors"],
            ]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_other_precedence(self):
        expression = "zeppelin \\union floyd \\left_outer_join_{year = year} doors;"
        expected = [
            [
                ["zeppelin"],
                "\\union",
                [["floyd"], "\\left_outer_join", [["year", "=", "year"]], ["doors"]],
            ]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_other_unary(self):
        expression = "\\project_{albums} zeppelin \\left_outer_join_{year = year} \\project_{albums} floyd;"
        expected = [
            [
                ["\\project", ["albums"], ["zeppelin"]],
                "\\left_outer_join",
                [["year", "=", "year"]],
                ["\\project", ["albums"], ["floyd"]],
            ]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    # Exceptions

    def test_exp_no_relations(self):
        expression = "\\left_outer_join_;"
        self.assertRaises(ParseException, self.parse, expression)

    def test_exp_left_relation(self):
        expression = "roger \\left_outer_join_{year = year};"
        self.assertRaises(ParseException, self.parse, expression)

    def test_exp_right_relation(self):
        expression = "\\left_outer_join_{year = year} floyd;"
        self.assertRaises(ParseException, self.parse, expression)

    def test_exp_empty_conditions(self):
        expression = "zeppelin \\left_outer_join_{} floyd;"
        self.assertRaises(ParseException, self.parse, expression)


class TestRightOuterJoin(GrammarTestCase):
    def setUp(self):
        self.parser = ExtendedGrammar()
        self.parse = self.parse_function(self.parser.statements)

    def test_simple(self):
        expression = "zeppelin \\right_outer_join_{year = year} floyd;"
        expected = [
            [["zeppelin"], "\\right_outer_join", [["year", "=", "year"]], ["floyd"]]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_multiple(self):
        expression = "zeppelin \\right_outer_join_{year = year} floyd \\right_outer_join_{year = year} doors;"
        expected = [
            [
                ["zeppelin"],
                "\\right_outer_join",
                [["year", "=", "year"]],
                ["floyd"],
                "\\right_outer_join",
                [["year", "=", "year"]],
                ["doors"],
            ]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_same_precedence(self):
        expression = "zeppelin \\right_outer_join_{year = year} floyd \\join doors;"
        expected = [
            [
                ["zeppelin"],
                "\\right_outer_join",
                [["year", "=", "year"]],
                ["floyd"],
                "\\join",
                ["doors"],
            ]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_other_precedence(self):
        expression = "zeppelin \\union floyd \\right_outer_join_{year = year} doors;"
        expected = [
            [
                ["zeppelin"],
                "\\union",
                [["floyd"], "\\right_outer_join", [["year", "=", "year"]], ["doors"]],
            ]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    def test_other_unary(self):
        expression = "\\project_{albums} zeppelin \\right_outer_join_{year = year} \\project_{albums} floyd;"
        expected = [
            [
                ["\\project", ["albums"], ["zeppelin"]],
                "\\right_outer_join",
                [["year", "=", "year"]],
                ["\\project", ["albums"], ["floyd"]],
            ]
        ]
        actual = self.parse(expression)
        self.assertEqual(expected, actual)

    # Exceptions

    def test_exp_no_relations(self):
        expression = "\\right_outer_join_;"
        self.assertRaises(ParseException, self.parse, expression)

    def test_exp_left_relation(self):
        expression = "roger \\right_outer_join_{year = year};"
        self.assertRaises(ParseException, self.parse, expression)

    def test_exp_right_relation(self):
        expression = "\\right_outer_join_{year = year} floyd;"
        self.assertRaises(ParseException, self.parse, expression)

    def test_exp_empty_conditions(self):
        expression = "zeppelin \\right_outer_join_{} floyd;"
        self.assertRaises(ParseException, self.parse, expression)
