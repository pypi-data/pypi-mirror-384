import functools

from rapt2.rapt import Rapt
from rapt2.transformers.sql import sql_translator
from rapt2.treebrd.grammars import CoreGrammar
from rapt2.treebrd.grammars.extended_grammar import ExtendedGrammar
from rapt2.treebrd.treebrd import TreeBRD
from tests.transformers.test_transfomer import TestTransformer


class TestSQLSequence(TestTransformer):
    grammar = CoreGrammar()

    def setUp(self):
        self.translate = self.translate_func(
            functools.partial(
                Rapt(grammar="Extended Grammar").to_sql_sequence, use_bag_semantics=True
            )
        )
        self.translate_set = self.translate_func(
            functools.partial(Rapt(grammar="Extended Grammar").to_sql_sequence)
        )


class TestRelation(TestSQLSequence):
    def test_single_relation(self):
        ra = "alpha;"
        expected = [["SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha"]]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_single_relation_set(self):
        ra = "alpha;"
        expected = [["SELECT DISTINCT alpha.a1, alpha.a2, alpha.a3 FROM alpha"]]
        actual = self.translate_set(ra)
        self.assertEqual(expected, actual)

    def test_multiple_relations(self):
        ra = "alpha; beta;"
        expected = [
            ["SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha"],
            ["SELECT beta.b1, beta.b2, beta.b3 FROM beta"],
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestSelect(TestSQLSequence):
    def test_single_select(self):
        ra = "\\select_{a1=a2} alpha;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha WHERE (a1 = a2)",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_multiple_select_with_multiple_conditions(self):
        ra = "\\select_{a1=2 or a1=1} \\select_{a2=2 or a2=1} alpha;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha WHERE ((a2 = 2) OR (a2 = 1))",
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha "
                "WHERE (((a2 = 2) OR (a2 = 1))) AND (((a1 = 2) OR (a1 = 1)))",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestProject(TestSQLSequence):
    def test_simple(self):
        ra = "\\project_{a1, a2} alpha;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT alpha.a1, alpha.a2 FROM alpha",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestRename(TestSQLSequence):
    def test_relation(self):
        ra = "\\rename_{apex} alpha;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT apex.a1, apex.a2, apex.a3 "
                "FROM (SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha) "
                "AS apex(a1, a2, a3)",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_rename_attributes(self):
        ra = "\\rename_{(a, b, c)} alpha;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT alpha.a, alpha.b, alpha.c "
                "FROM (SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha) "
                "AS alpha(a, b, c)",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_rename_all(self):
        ra = "\\rename_{apex(a, b, c)} alpha;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT apex.a, apex.b, apex.c "
                "FROM (SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha) "
                "AS apex(a, b, c)",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestAssignment(TestSQLSequence):
    def test_relation(self):
        ra = "newalpha := alpha;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "CREATE TEMPORARY TABLE newalpha(a1, a2, a3) AS "
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestJoin(TestSQLSequence):
    def test_relation(self):
        ra = "alpha \\join beta;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT beta.b1, beta.b2, beta.b3 FROM beta",
                "SELECT alpha.a1, alpha.a2, alpha.a3, "
                "beta.b1, beta.b2, beta.b3 FROM "
                "(SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha) AS alpha "
                "CROSS JOIN "
                "(SELECT beta.b1, beta.b2, beta.b3 FROM beta) AS beta",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_three_relations(self):
        self.maxDiff = None
        ra = "alpha \\join beta \\join gamma;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT beta.b1, beta.b2, beta.b3 FROM beta",
                "SELECT alpha.a1, alpha.a2, alpha.a3, beta.b1, beta.b2, "
                "beta.b3 FROM "
                "(SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha) AS alpha "
                "CROSS JOIN "
                "(SELECT beta.b1, beta.b2, beta.b3 FROM beta) AS beta",
                "SELECT gamma.g1, gamma.g2 FROM gamma",
                "SELECT alpha.a1, alpha.a2, alpha.a3, beta.b1, beta.b2, "
                "beta.b3, gamma.g1, gamma.g2 FROM "
                "(SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha) AS alpha "
                "CROSS JOIN "
                "(SELECT beta.b1, beta.b2, beta.b3 FROM beta) AS beta "
                "CROSS JOIN "
                "(SELECT gamma.g1, gamma.g2 FROM gamma) AS gamma",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestNaturalJoin(TestSQLSequence):
    grammar = ExtendedGrammar()

    def test_relation_simple(self):
        ra = "alpha \\natural_join alphatwin;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT alphatwin.a1, alphatwin.a2, alphatwin.a3 FROM alphatwin",
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM "
                "(SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha) AS alpha "
                "NATURAL JOIN "
                "(SELECT alphatwin.a1, alphatwin.a2, alphatwin.a3 "
                "FROM alphatwin) AS alphatwin",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestThetaJoin(TestSQLSequence):
    grammar = ExtendedGrammar()

    def test_relation(self):
        ra = "alpha \\join_{a1 = b1} beta;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT beta.b1, beta.b2, beta.b3 FROM beta",
                "SELECT alpha.a1, alpha.a2, alpha.a3, "
                "beta.b1, beta.b2, beta.b3 FROM "
                "(SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha) AS alpha "
                "JOIN "
                "(SELECT beta.b1, beta.b2, beta.b3 FROM beta) AS beta "
                "ON (a1 = b1)",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestSet:
    __test__ = False

    def test_simple(self):
        ra = "gamma {operator} gammatwin;".format(operator=self.ra_operator)

        root_list = TreeBRD(self.grammar).build(instring=ra, schema=self.schema)
        name = id(root_list[0])
        root_list = root_list[0].post_order()
        actual = sql_translator.translate(root_list, use_bag_semantics=True)

        expected = [
            "SELECT gamma.g1, gamma.g2 FROM gamma",
            "SELECT gammatwin.g1, gammatwin.g2 FROM gammatwin",
            "SELECT g1, g2 FROM ("
            "SELECT gamma.g1, gamma.g2 FROM gamma "
            "{operator} ALL "
            "SELECT gammatwin.g1, gammatwin.g2 FROM gammatwin) "
            "AS _{name}".format(operator=self.sql_operator, name=name),
        ]
        self.assertEqual(expected, actual)

    def test_simple_multiple(self):
        ra = "gamma {operator} gammatwin {operator} gammaprime;".format(
            operator=self.ra_operator
        )

        root_list = TreeBRD(self.grammar).build(instring=ra, schema=self.schema)
        root_name = id(root_list[0])
        child_name = id(root_list[0].left)
        root_list = root_list[0].post_order()
        actual = sql_translator.translate(root_list, use_bag_semantics=True)

        expected = [
            "SELECT gamma.g1, gamma.g2 FROM gamma",
            "SELECT gammatwin.g1, gammatwin.g2 FROM gammatwin",
            "SELECT g1, g2 FROM (SELECT gamma.g1, gamma.g2 FROM gamma "
            "{operator} ALL "
            "SELECT gammatwin.g1, gammatwin.g2 FROM gammatwin) AS _{name1}".format(
                operator=self.sql_operator,
                name1=child_name,
            ),
            "SELECT gammaprime.g1, gammaprime.g2 FROM gammaprime",
            "SELECT g1, g2 FROM ("
            "SELECT g1, g2 FROM "
            "(SELECT gamma.g1, gamma.g2 FROM gamma "
            "{operator} ALL "
            "SELECT gammatwin.g1, gammatwin.g2 FROM gammatwin) AS _{name1} "
            "{operator} ALL "
            "SELECT gammaprime.g1, gammaprime.g2 FROM gammaprime) AS _{name2}".format(
                operator=self.sql_operator, name1=child_name, name2=root_name
            ),
        ]
        self.assertEqual(expected, actual)


class TestUnion(TestSQLSequence, TestSet):
    ra_operator = "\\union"
    sql_operator = "UNION"


class TestDifference(TestSQLSequence, TestSet):
    ra_operator = "\\difference"
    sql_operator = "EXCEPT"


class TestIntersection(TestSQLSequence, TestSet):
    grammar = ExtendedGrammar()
    ra_operator = "\\intersect"
    sql_operator = "INTERSECT"


class TestDefined(TestSQLSequence):
    def test_simple_defined(self):
        ra = "\\select_{defined(a1)} alpha;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha WHERE a1 IS NOT NULL",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_not_defined(self):
        ra = "\\select_{not defined(a1)} alpha;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha WHERE NOT a1 IS NOT NULL",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_defined_and_defined(self):
        ra = "\\select_{defined(a1) and defined(a2)} alpha;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha WHERE (a1 IS NOT NULL AND a2 IS NOT NULL)",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_defined_or_defined(self):
        ra = "\\select_{defined(a1) or defined(a2)} alpha;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha WHERE (a1 IS NOT NULL OR a2 IS NOT NULL)",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_defined_with_equality(self):
        ra = "\\select_{defined(a1) and a1=5} alpha;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha WHERE (a1 IS NOT NULL AND (a1 = 5))",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_not_defined_with_equality(self):
        ra = "\\select_{not defined(a1) or a2=10} alpha;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha WHERE (NOT a1 IS NOT NULL OR (a2 = 10))",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_complex_defined_condition(self):
        ra = "\\select_{defined(a1) and (a2=5 or not defined(a3))} alpha;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha WHERE (a1 IS NOT NULL AND ((a2 = 5) OR NOT a3 IS NOT NULL))",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_defined_with_relation_attribute(self):
        ra = "\\select_{defined(alpha.a1)} alpha;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha WHERE alpha.a1 IS NOT NULL",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_multiple_defined_conditions(self):
        ra = "\\select_{defined(a1)} \\select_{defined(a2)} alpha;"
        expected = [
            [
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha",
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha WHERE a2 IS NOT NULL",
                "SELECT alpha.a1, alpha.a2, alpha.a3 FROM alpha WHERE (a2 IS NOT NULL) AND (a1 IS NOT NULL)",
            ]
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)
