import functools
from unittest import TestCase

import psycopg2

from rapt2 import Rapt


class TestTranslator(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = psycopg2.connect(
            database="rapt_test_db", user="raptor", password="raptolicious"
        )
        cls.cur = cls.conn.cursor()
        cls.execute = cls.cur.execute

        cls.setup_database(cls.schema, cls.data)

        cls.translate_bag = staticmethod(
            cls.translate_func(
                functools.partial(
                    Rapt(grammar="Extended Grammar").to_sql, use_bag_semantics=True
                )
            )
        )
        cls.translate_set = staticmethod(
            cls.translate_func(
                functools.partial(Rapt(grammar="Extended Grammar").to_sql)
            )
        )

    @classmethod
    def translate_func(cls, func, schema=None):
        schema = schema or cls.schema
        return functools.partial(func, schema=schema)

    @classmethod
    def tearDownClass(cls):
        cls.drop_tables(cls.schema.keys())

    @classmethod
    def setup_database(cls, schema, data):
        cls.create_tables(schema)
        cls.insert_data(data)

    @classmethod
    def create_tables(cls, schema):
        for relation, attributes in schema.items():
            attributes = ", ".join(
                ["{} text".format(attribute) for attribute in attributes]
            )
            statement = "CREATE TABLE %s (%s)" % (relation, attributes)
            cls.execute(statement)

    @classmethod
    def drop_tables(cls, tables):
        for relation in tables:
            statement = "DROP TABLE %s;" % relation
            cls.execute(statement)

    @classmethod
    def insert_data(cls, data_set):
        for relation, data in data_set.items():
            values = ", ".join(["%s" for _ in data[0]])
            statement = "INSERT INTO {0} VALUES ({1})".format(relation, values)
            for row in data:
                cls.execute(statement, row)

    @classmethod
    def query(cls, statement):
        cls.execute(statement)
        return cls.cur.fetchall()

    @classmethod
    def query_list(cls, statements):
        for statement in statements:
            cls.execute(statement)
        return cls.cur.fetchall()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()


class TestRelation(TestTranslator):
    @classmethod
    def setUpClass(cls):
        cls.schema = {"Alpha": ["a1", "a2"]}
        cls.data = {"Alpha": [("1", "a"), ("2", "b"), ("2", "b")]}
        super().setUpClass()

    def test_single_relation_set(self):
        instring = "alpha;"
        translation = self.translate_set(instring)
        expected = [("1", "a"), ("2", "b")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_relation_set_cased(self):
        instring = "Alpha;"
        translation = self.translate_set(instring)
        expected = [("1", "a"), ("2", "b")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_relation_bag(self):
        instring = "alpha;"
        translation = self.translate_bag(instring)
        expected = [("1", "a"), ("2", "b"), ("2", "b")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_multiple_relations_bag(self):
        instring = "alpha; alpha;"
        translation = self.translate_bag(instring)
        expected = [("1", "a"), ("2", "b"), ("2", "b")]
        self.assertCountEqual(expected, self.query_list(translation))


class TestProject(TestTranslator):
    @classmethod
    def setUpClass(cls):
        cls.schema = {"alpha": ["a1", "a2", "a3"]}
        cls.data = {"alpha": [("1", "a", "!"), ("2", "b", "!"), ("3", "b", "!")]}
        super().setUpClass()

    def test_single_project_single_attr_set_no_duplicates(self):
        instring = r"\project_{a1} alpha;"
        translation = self.translate_set(instring)
        expected = [("1",), ("2",), ("3",)]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_project_single_attr_set_no_duplicates_cased(self):
        instring = r"\project_{a1} ALPHA;"
        translation = self.translate_set(instring)
        expected = [("1",), ("2",), ("3",)]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_project_single_attr_set_with_duplicates(self):
        instring = r"\project_{a2} alpha;"
        translation = self.translate_set(instring)
        expected = [("a",), ("b",)]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_project_single_attr_bag_no_duplicates(self):
        instring = r"\project_{a1} alpha;"
        translation = self.translate_bag(instring)
        expected = [("1",), ("2",), ("3",)]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_project_single_attr_bag_with_duplicates(self):
        instring = r"\project_{a2} alpha;"
        translation = self.translate_bag(instring)
        expected = [("a",), ("b",), ("b",)]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_project_two_attr_set_no_duplicates(self):
        instring = r"\project_{a1, a2} alpha;"
        translation = self.translate_set(instring)
        expected = [
            (
                "1",
                "a",
            ),
            ("2", "b"),
            ("3", "b"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_project_two_attr_set_with_duplicates(self):
        instring = r"\project_{a2, a3} alpha;"
        translation = self.translate_set(instring)
        expected = [
            (
                "a",
                "!",
            ),
            ("b", "!"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_project_two_attr_bag_no_duplicates(self):
        instring = r"\project_{a1, a2} alpha;"
        translation = self.translate_bag(instring)
        expected = [
            (
                "1",
                "a",
            ),
            ("2", "b"),
            ("3", "b"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_project_two_attr_bag_with_duplicates(self):
        instring = r"\project_{a2, a3} alpha;"
        translation = self.translate_bag(instring)
        expected = [
            (
                "a",
                "!",
            ),
            ("b", "!"),
            ("b", "!"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_project_all_attr(self):
        instring = r"\project_{a1, a2, a3} alpha;"
        translation = self.translate_set(instring)
        expected = self.data["alpha"]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_project_all_attr_out_of_order(self):
        instring = r"\project_{a2, a3, a1} alpha;"
        translation = self.translate_set(instring)
        expected = [("a", "!", "1"), ("b", "!", "2"), ("b", "!", "3")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_double_project(self):
        instring = r"\project_{a2} \project_{a2, a3} alpha;"
        translation = self.translate_set(instring)
        expected = [("a",), ("b",)]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_triple_project(self):
        instring = (
            r"\project_{a1} \project_{a2, a1}"
            r"\project_{a2, a1, a3} alpha;"
        )
        translation = self.translate_set(instring)
        expected = [("1",), ("2",), ("3",)]
        self.assertCountEqual(expected, self.query_list(translation))


class TestSelect(TestTranslator):
    @classmethod
    def setUpClass(cls):
        cls.schema = {"alpha": ["a1", "a2", "a3"]}
        cls.data = {"alpha": [("1", "a", "!"), ("2", "b", "!"), ("2", "b", "!")]}
        super().setUpClass()

    def test_single_select_with_no_attr_set(self):
        instring = r"\select_{1=1} alpha;"
        translation = self.translate_set(instring)
        expected = [("1", "a", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_select_with_no_attr_bag(self):
        instring = r"\select_{1=1} alpha;"
        translation = self.translate_bag(instring)
        expected = self.data["alpha"]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_select_with_attr_all(self):
        instring = r"\select_{a1<>'missing'} alpha;"
        translation = self.translate_set(instring)
        expected = [("1", "a", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_select_with_attr_subset_set(self):
        instring = r"\select_{a1<>'1'} alpha;"
        translation = self.translate_set(instring)
        expected = [("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_select_with_attr_subset_bag(self):
        instring = r"\select_{a1<>'1'} alpha;"
        translation = self.translate_bag(instring)
        expected = [("2", "b", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_select_with_attr_none(self):
        instring = r"\select_{a1='1' and a2='b'} alpha;"
        translation = self.translate_set(instring)
        expected = []
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_select_with_multiple_cond_attr_subset_set(self):
        instring = r"\select_{a1<>'1' and a2<>'a'} alpha;"
        translation = self.translate_set(instring)
        expected = [("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_single_select_with_attr_case(self):
        instring = r"\select_{A1='1' and A2='b'} Alpha;"
        translation = self.translate_set(instring)
        expected = []
        self.assertCountEqual(expected, self.query_list(translation))

    def test_double_select_with_attr(self):
        instring = r"\select_{a1!='missing'} \select_{A2!='missing'} Alpha;"
        translation = self.translate_set(instring)
        expected = [("1", "a", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))


class TestRename(TestTranslator):
    @classmethod
    def setUpClass(cls):
        cls.schema = {"alpha": ["a1", "a2", "a3"]}
        cls.data = {"alpha": [("1", "a", "!"), ("2", "b", "!"), ("2", "b", "!")]}
        super().setUpClass()

    def test_rename_relation(self):
        instring = (
            r"\project_{AlphaPrime.a1, AlphaPrime.a2, AlphaPrime.a3} "
            r"\rename_{AlphaPrime} alpha;"
        )
        translation = self.translate_set(instring)
        expected = [("1", "a", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_rename_relation_bag(self):
        instring = (
            r"\project_{AlphaPrime.a1, AlphaPrime.a2, AlphaPrime.a3} "
            r"\rename_{AlphaPrime} alpha;"
        )
        translation = self.translate_bag(instring)
        expected = [("1", "a", "!"), ("2", "b", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_rename_attributes(self):
        instring = (
            r"\project_{alpha.ap1, alpha.ap2, alpha.ap3} "
            r"\rename_{(ap1, ap2, ap3)} alpha;"
        )
        translation = self.translate_set(instring)
        expected = [("1", "a", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_rename_relation_and_attributes(self):
        instring = (
            r"\project_{APrime.ap1, APrime.ap2, APrime.ap3} "
            r"\rename_{APrime(ap1, ap2, ap3)} alpha;"
        )
        translation = self.translate_set(instring)
        expected = [("1", "a", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))


class TestAssign(TestTranslator):
    @classmethod
    def setUpClass(cls):
        cls.schema = {"alpha": ["a1", "a2", "a3"]}
        cls.data = {"alpha": [("1", "a", "!"), ("2", "b", "!"), ("2", "b", "!")]}
        super().setUpClass()

    def tearDown(self):
        self.drop_tables(["alpha_prime"])

    def test_assign_relation_set(self):
        instring = "alpha_prime := alpha; alpha_prime;"
        translation = self.translate_set(instring)
        expected = [("1", "a", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_assign_relation_bag(self):
        instring = "alpha_prime := alpha; alpha_prime;"
        translation = self.translate_bag(instring)
        expected = [("1", "a", "!"), ("2", "b", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_assign_relation_with_attr_rename(self):
        instring = (
            r"alpha_prime(ap1, ap2, ap3) := alpha;"
            r"\project_{alpha_prime.ap1, alpha_prime.ap2, alpha_prime.ap3} alpha_prime;"
        )
        translation = self.translate_set(instring)
        expected = [("1", "a", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))


class TestUnion(TestTranslator):
    @classmethod
    def setUpClass(cls):
        attrs = ["a1", "a2", "a3"]
        cls.schema = {
            "alpha": attrs,
            "alpha_copy": attrs,
            "alpha_subset": attrs,
            "alpha_superset": attrs,
            "alpha_extra": attrs,
        }
        cls.data = {
            "alpha": [("1", "a", "!"), ("2", "b", "!"), ("2", "b", "!")],
            "alpha_copy": [("1", "a", "!"), ("2", "b", "!"), ("2", "b", "!")],
            "alpha_subset": [
                ("1", "a", "!"),
            ],
            "alpha_superset": [
                ("1", "a", "!"),
                ("2", "b", "!"),
                ("2", "b", "!"),
                ("3", "c", "?"),
            ],
            "alpha_extra": [
                ("3", "c", "?"),
            ],
        }
        super().setUpClass()

    def test_union_self_set(self):
        instring = "alpha \\union alpha;"
        translation = self.translate_set(instring)
        expected = [("1", "a", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_union_self_bag(self):
        instring = "alpha \\union alpha;"
        translation = self.translate_bag(instring)
        expected = [
            ("1", "a", "!"),
            ("2", "b", "!"),
            ("2", "b", "!"),
            ("1", "a", "!"),
            ("2", "b", "!"),
            ("2", "b", "!"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_union_other_set(self):
        instring = "alpha \\union alpha_copy;"
        translation = self.translate_set(instring)
        expected = [("1", "a", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_union_other_bag(self):
        instring = "alpha \\union alpha_copy;"
        translation = self.translate_bag(instring)
        expected = [
            ("1", "a", "!"),
            ("2", "b", "!"),
            ("2", "b", "!"),
            ("1", "a", "!"),
            ("2", "b", "!"),
            ("2", "b", "!"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_union_superset_set(self):
        instring = "alpha \\union alpha_superset;"
        translation = self.translate_set(instring)
        expected = [("1", "a", "!"), ("2", "b", "!"), ("3", "c", "?")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_union_superset_bag(self):
        instring = "alpha \\union alpha_superset;"
        translation = self.translate_bag(instring)
        expected = [
            ("1", "a", "!"),
            ("2", "b", "!"),
            ("2", "b", "!"),
            ("1", "a", "!"),
            ("2", "b", "!"),
            ("2", "b", "!"),
            ("3", "c", "?"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_union_extra_set(self):
        instring = "alpha \\union alpha_extra;"
        translation = self.translate_set(instring)
        expected = [("1", "a", "!"), ("2", "b", "!"), ("3", "c", "?")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_union_extra_bag(self):
        instring = "alpha \\union alpha_extra;"
        translation = self.translate_bag(instring)
        expected = [("1", "a", "!"), ("2", "b", "!"), ("2", "b", "!"), ("3", "c", "?")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_union_subset_set(self):
        instring = "alpha \\union alpha_subset;"
        translation = self.translate_set(instring)
        expected = [("1", "a", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_union_subset_bag(self):
        instring = "alpha \\union alpha_extra;"
        translation = self.translate_bag(instring)
        expected = [("1", "a", "!"), ("2", "b", "!"), ("2", "b", "!"), ("3", "c", "?")]
        self.assertCountEqual(expected, self.query_list(translation))


class TestDifference(TestTranslator):
    @classmethod
    def setUpClass(cls):
        attrs = ["a1", "a2", "a3"]
        cls.schema = {
            "alpha": attrs,
            "alpha_copy": attrs,
            "alpha_subset": attrs,
            "alpha_superset": attrs,
            "alpha_extra": attrs,
        }
        cls.data = {
            "alpha": [("1", "a", "!"), ("2", "b", "!"), ("2", "b", "!")],
            "alpha_copy": [("1", "a", "!"), ("2", "b", "!"), ("2", "b", "!")],
            "alpha_subset": [
                ("1", "a", "!"),
            ],
            "alpha_superset": [
                ("1", "a", "!"),
                ("2", "b", "!"),
                ("2", "b", "!"),
                ("3", "c", "?"),
                ("3", "c", "?"),
            ],
            "alpha_extra": [
                ("3", "c", "?"),
                ("3", "c", "?"),
            ],
        }
        super().setUpClass()

    def test_difference_self_set(self):
        instring = "alpha \\difference alpha;"
        translation = self.translate_set(instring)
        expected = []
        self.assertCountEqual(expected, self.query_list(translation))

    def test_difference_self_bag(self):
        instring = "alpha \\difference alpha;"
        translation = self.translate_bag(instring)
        expected = []
        self.assertCountEqual(expected, self.query_list(translation))

    def test_difference_other_set(self):
        instring = "alpha \\difference alpha_copy;"
        translation = self.translate_set(instring)
        expected = []
        self.assertCountEqual(expected, self.query_list(translation))

    def test_difference_other_bag(self):
        instring = "alpha \\difference alpha_copy;"
        translation = self.translate_set(instring)
        expected = []
        self.assertCountEqual(expected, self.query_list(translation))

    def test_difference_subset_set(self):
        instring = "alpha_subset \\difference alpha;"
        translation = self.translate_set(instring)
        expected = []
        self.assertCountEqual(expected, self.query_list(translation))

    def test_difference_subset_bag(self):
        instring = "alpha_subset \\difference alpha;"
        translation = self.translate_bag(instring)
        expected = []
        self.assertCountEqual(expected, self.query_list(translation))

    def test_difference_superset_set(self):
        instring = "alpha_superset \\difference alpha;"
        translation = self.translate_set(instring)
        expected = [("3", "c", "?")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_difference_superset_bag(self):
        instring = "alpha_superset \\difference alpha;"
        translation = self.translate_bag(instring)
        expected = [("3", "c", "?"), ("3", "c", "?")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_difference_extra_set(self):
        instring = "alpha_extra \\difference alpha;"
        translation = self.translate_set(instring)
        expected = [("3", "c", "?")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_difference_extra_bag(self):
        instring = "alpha_extra \\difference alpha;"
        translation = self.translate_bag(instring)
        expected = [("3", "c", "?"), ("3", "c", "?")]
        self.assertCountEqual(expected, self.query_list(translation))


class TestIntersection(TestTranslator):
    @classmethod
    def setUpClass(cls):
        attrs = ["a1", "a2", "a3"]
        cls.schema = {
            "alpha": attrs,
            "alpha_copy": attrs,
            "alpha_subset": attrs,
            "alpha_superset": attrs,
            "alpha_extra": attrs,
        }
        cls.data = {
            "alpha": [("1", "a", "!"), ("2", "b", "!"), ("2", "b", "!")],
            "alpha_copy": [("1", "a", "!"), ("2", "b", "!"), ("2", "b", "!")],
            "alpha_subset": [
                ("1", "a", "!"),
            ],
            "alpha_superset": [
                ("1", "a", "!"),
                ("2", "b", "!"),
                ("2", "b", "!"),
                ("3", "c", "?"),
                ("3", "c", "?"),
            ],
            "alpha_extra": [
                ("3", "c", "?"),
                ("3", "c", "?"),
            ],
        }
        super().setUpClass()

    def test_intersect_self_set(self):
        instring = "alpha \\intersect alpha;"
        translation = self.translate_set(instring)
        expected = [("1", "a", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_intersect_self_bag(self):
        instring = "alpha \\intersect alpha;"
        translation = self.translate_bag(instring)
        expected = [("1", "a", "!"), ("2", "b", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_intersect_other_set(self):
        instring = "alpha \\intersect alpha_copy;"
        translation = self.translate_set(instring)
        expected = [("1", "a", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_intersect_other_bag(self):
        instring = "alpha \\intersect alpha_copy;"
        translation = self.translate_bag(instring)
        expected = [("1", "a", "!"), ("2", "b", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_intersect_superset_set(self):
        instring = "alpha \\intersect alpha_superset;"
        translation = self.translate_set(instring)
        expected = [("1", "a", "!"), ("2", "b", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_intersect_superset_bag(self):
        instring = "alpha \\intersect alpha_superset;"
        translation = self.translate_bag(instring)
        expected = [
            ("1", "a", "!"),
            ("2", "b", "!"),
            ("2", "b", "!"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_intersect_extra_set(self):
        instring = "alpha_extra \\intersect alpha;"
        translation = self.translate_set(instring)
        expected = []
        self.assertCountEqual(expected, self.query_list(translation))

    def test_intersect_extra_bag(self):
        instring = "alpha_extra \\intersect alpha;"
        translation = self.translate_bag(instring)
        expected = []
        self.assertCountEqual(expected, self.query_list(translation))

    def test_intersect_subset_set(self):
        instring = "alpha \\intersect alpha_subset;"
        translation = self.translate_set(instring)
        expected = [("1", "a", "!")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_intersect_subset_bag(self):
        instring = "alpha \\intersect alpha_subset;"
        translation = self.translate_bag(instring)
        expected = [("1", "a", "!")]
        self.assertCountEqual(expected, self.query_list(translation))


class TestJoin(TestTranslator):
    @classmethod
    def setUpClass(cls):
        cls.schema = {
            "alpha": ["a1", "a2"],
            "beta": ["b1"],
            "gamma": ["g1"],
        }
        cls.data = {
            "alpha": [("1", "a"), ("2", "b"), ("2", "b")],
            "beta": [
                ("3",),
                ("4",),
            ],
            "gamma": [("?",), ("!",)],
        }
        super().setUpClass()

    def test_join_other_set(self):
        instring = "alpha \\join beta;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "3"),
            ("2", "b", "3"),
            ("1", "a", "4"),
            ("2", "b", "4"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_join_other_bag(self):
        instring = "alpha \\join beta;"
        translation = self.translate_bag(instring)
        expected = [
            ("1", "a", "3"),
            ("2", "b", "3"),
            ("2", "b", "3"),
            ("1", "a", "4"),
            ("2", "b", "4"),
            ("2", "b", "4"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_join_double(self):
        instring = "alpha \\join beta \\join gamma;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "3", "?"),
            ("2", "b", "3", "?"),
            ("1", "a", "4", "?"),
            ("2", "b", "4", "?"),
            ("1", "a", "3", "!"),
            ("2", "b", "3", "!"),
            ("1", "a", "4", "!"),
            ("2", "b", "4", "!"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_join_self_with_rename_set(self):
        instring = "\\rename_{a1} alpha \\join \\rename_{a2} alpha;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "1", "a"),
            ("2", "b", "1", "a"),
            ("1", "a", "2", "b"),
            ("2", "b", "2", "b"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))


class TestNaturalJoin(TestTranslator):
    @classmethod
    def setUpClass(cls):
        cls.schema = {
            "alpha": ["a1", "a2"],
            "alpha_copy": ["a1", "a2"],
            "alpha_subset": ["a1", "a2"],
            "alpha_prime": ["a1", "ap2"],
            "alpha_prime_extra": ["ap2", "ap3"],
        }
        cls.data = {
            "alpha": [("1", "a"), ("2", "b"), ("2", "b")],
            "alpha_copy": [("1", "a"), ("2", "b"), ("2", "b")],
            "alpha_subset": [("2", "b"), ("2", "b")],
            "alpha_prime": [("1", "!"), ("2", "?")],
            "alpha_prime_extra": [("?", "this")],
        }
        super().setUpClass()

    def test_join_copy_set(self):
        instring = "alpha \\natural_join alpha_copy;"
        translation = self.translate_set(instring)
        expected = [("1", "a"), ("2", "b")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_join_copy_bag(self):
        instring = "alpha \\natural_join alpha_copy;"
        translation = self.translate_bag(instring)
        expected = [
            ("1", "a"),
            ("2", "b"),
            ("2", "b"),
            ("1", "a"),
            ("2", "b"),
            ("2", "b"),
        ]
        self.assertCountEqual(set(expected), set(self.query_list(translation)))

    def test_join_prime_set(self):
        instring = "alpha \\natural_join alpha_prime;"
        translation = self.translate_set(instring)
        expected = [("1", "a", "!"), ("2", "b", "?")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_join_prime_bag(self):
        instring = "alpha \\natural_join alpha_prime;"
        translation = self.translate_bag(instring)
        expected = [("1", "a", "!"), ("2", "b", "?"), ("2", "b", "?")]
        self.assertCountEqual(set(expected), set(self.query_list(translation)))

    def test_join_prime_extra_set(self):
        instring = "alpha \\natural_join alpha_prime \\natural_join alpha_prime_extra;"
        translation = self.translate_set(instring)
        expected = [("2", "b", "?", "this")]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_join_prime_extra_bag(self):
        instring = "alpha \\natural_join alpha_prime \\natural_join alpha_prime_extra;"
        translation = self.translate_bag(instring)
        expected = [
            ("2", "b", "?", "this"),
            ("2", "b", "?", "this"),
        ]
        self.assertCountEqual(set(expected), set(self.query_list(translation)))

    def test_join_self_with_rename_set(self):
        instring = "\\rename_{a1} alpha \\natural_join \\rename_{a2} alpha;"
        translation = self.translate_set(instring)
        expected = [("1", "a"), ("2", "b")]
        self.assertCountEqual(expected, self.query_list(translation))


class TestThetaJoin(TestTranslator):
    @classmethod
    def setUpClass(cls):
        cls.schema = {
            "alpha": ["a1", "a2"],
            "alpha_copy": ["a1", "a2"],
            "alpha_prime": ["ap1", "ap2"],
            "alpha_prime_subset": ["ap1", "ap2"],
        }
        cls.data = {
            "alpha": [("1", "a"), ("2", "b"), ("2", "b")],
            "alpha_copy": [("1", "a"), ("2", "b"), ("2", "b")],
            "alpha_prime": [("1", "a"), ("2", "b"), ("2", "b")],
            "alpha_prime_subset": [("1", "!")],
        }
        super().setUpClass()

    def test_join_copy_set(self):
        instring = "alpha \\join_{alpha.a1=alpha_copy.a1} alpha_copy;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "1", "a"),
            ("2", "b", "2", "b"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_join_copy_bag(self):
        instring = "alpha \\join_{alpha.a1=alpha_copy.a1} alpha_copy;"
        translation = self.translate_bag(instring)
        expected = [
            ("1", "a", "1", "a"),
            ("2", "b", "2", "b"),
            ("2", "b", "2", "b"),
        ]
        self.assertCountEqual(set(expected), set(self.query_list(translation)))

    def test_join_prime_set(self):
        instring = "alpha \\join_{alpha.a1=alpha_prime.ap1} alpha_prime;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "1", "a"),
            ("2", "b", "2", "b"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))


class TestUnary(TestTranslator):
    @classmethod
    def setUpClass(cls):
        cls.schema = {"Alpha": ["a1", "a2"]}
        cls.data = {"Alpha": [("1", "a"), ("2", "b"), ("2", "b")]}
        super().setUpClass()

    def test_select_project(self):
        instring = r"\select_{a2='b'} \project_{a2 } alpha;"
        translation = self.translate_set(instring)
        expected = [("b",)]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_project_select(self):
        instring = r" \project_{a2} \select_{a2='b'} alpha;"
        translation = self.translate_set(instring)
        expected = [("b",)]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_select_rename(self):
        instring = r"\select_{ap2='b'} \rename_{A(ap1, ap2)} alpha;"
        translation = self.translate_set(instring)
        expected = [
            (
                "2",
                "b",
            )
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_project_rename(self):
        instring = r"\project_{ap2} \rename_{A(ap1, ap2)} alpha;"
        translation = self.translate_set(instring)
        expected = [("a",), ("b",)]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_assign_project_rename(self):
        instring = r"A := \project_{ap2} \rename_{A(ap1, ap2)} alpha; A;"
        translation = self.translate_set(instring)
        expected = [("a",), ("b",)]
        self.assertCountEqual(expected, self.query_list(translation))


class TestFullOuterJoin(TestTranslator):
    @classmethod
    def setUpClass(cls):
        cls.schema = {
            "alpha": ["a1", "a2"],
            "beta": ["b1", "b2"],
            "gamma": ["g1", "g2"],
        }
        cls.data = {
            "alpha": [("1", "a"), ("2", "b"), ("3", "c")],
            "beta": [("1", "x"), ("2", "y"), ("4", "z")],
            "gamma": [("5", "p"), ("6", "q")],
        }
        super().setUpClass()

    def test_full_outer_join_basic_set(self):
        instring = "alpha \\full_outer_join_{a1 = b1} beta;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "1", "x"),
            ("2", "b", "2", "y"),
            ("3", "c", None, None),
            (None, None, "4", "z"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_full_outer_join_basic_bag(self):
        instring = "alpha \\full_outer_join_{a1 = b1} beta;"
        translation = self.translate_bag(instring)
        expected = [
            ("1", "a", "1", "x"),
            ("2", "b", "2", "y"),
            ("3", "c", None, None),
            (None, None, "4", "z"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_full_outer_join_complex_condition_set(self):
        instring = "alpha \\full_outer_join_{alpha.a1 = beta.b1 and a2 = 'a'} beta;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "1", "x"),
            ("2", "b", None, None),
            ("3", "c", None, None),
            (None, None, "2", "y"),
            (None, None, "4", "z"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_full_outer_join_with_project_set(self):
        instring = (
            "\\project_{alpha.a1, beta.b1} (alpha \\full_outer_join_{a1 = b1} beta);"
        )
        translation = self.translate_set(instring)
        expected = [
            ("1", "1"),
            ("2", "2"),
            ("3", None),
            (None, "4"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_full_outer_join_with_select_set(self):
        instring = "\\select_{alpha.a1 > '1'} (alpha \\full_outer_join_{a1 = b1} beta);"
        translation = self.translate_set(instring)
        expected = [
            ("2", "b", "2", "y"),
            ("3", "c", None, None),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_full_outer_join_chained_set(self):
        instring = "(alpha \\full_outer_join_{a1 = b1} beta) \\join gamma;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "1", "x", "5", "p"),
            ("1", "a", "1", "x", "6", "q"),
            ("2", "b", "2", "y", "5", "p"),
            ("2", "b", "2", "y", "6", "q"),
            ("3", "c", None, None, "5", "p"),
            ("3", "c", None, None, "6", "q"),
            (None, None, "4", "z", "5", "p"),
            (None, None, "4", "z", "6", "q"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))


class TestLeftOuterJoin(TestTranslator):
    @classmethod
    def setUpClass(cls):
        cls.schema = {
            "alpha": ["a1", "a2"],
            "beta": ["b1", "b2"],
            "gamma": ["g1", "g2"],
        }
        cls.data = {
            "alpha": [("1", "a"), ("2", "b"), ("3", "c")],
            "beta": [("1", "x"), ("2", "y"), ("4", "z")],
            "gamma": [("5", "p"), ("6", "q")],
        }
        super().setUpClass()

    def test_left_outer_join_basic_set(self):
        instring = "alpha \\left_outer_join_{a1 = b1} beta;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "1", "x"),
            ("2", "b", "2", "y"),
            ("3", "c", None, None),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_left_outer_join_basic_bag(self):
        instring = "alpha \\left_outer_join_{a1 = b1} beta;"
        translation = self.translate_bag(instring)
        expected = [
            ("1", "a", "1", "x"),
            ("2", "b", "2", "y"),
            ("3", "c", None, None),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_left_outer_join_complex_condition_set(self):
        instring = "alpha \\left_outer_join_{alpha.a1 = beta.b1 and a2 = 'a'} beta;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "1", "x"),
            ("2", "b", None, None),
            ("3", "c", None, None),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_left_outer_join_with_project_set(self):
        instring = (
            "\\project_{alpha.a1, beta.b1} (alpha \\left_outer_join_{a1 = b1} beta);"
        )
        translation = self.translate_set(instring)
        expected = [
            ("1", "1"),
            ("2", "2"),
            ("3", None),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_left_outer_join_with_select_set(self):
        instring = "\\select_{alpha.a1 > '1'} (alpha \\left_outer_join_{a1 = b1} beta);"
        translation = self.translate_set(instring)
        expected = [
            ("2", "b", "2", "y"),
            ("3", "c", None, None),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_left_outer_join_chained_set(self):
        instring = "(alpha \\left_outer_join_{a1 = b1} beta) \\join gamma;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "1", "x", "5", "p"),
            ("1", "a", "1", "x", "6", "q"),
            ("2", "b", "2", "y", "5", "p"),
            ("2", "b", "2", "y", "6", "q"),
            ("3", "c", None, None, "5", "p"),
            ("3", "c", None, None, "6", "q"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))


class TestRightOuterJoin(TestTranslator):
    @classmethod
    def setUpClass(cls):
        cls.schema = {
            "alpha": ["a1", "a2"],
            "beta": ["b1", "b2"],
            "gamma": ["g1", "g2"],
        }
        cls.data = {
            "alpha": [("1", "a"), ("2", "b"), ("3", "c")],
            "beta": [("1", "x"), ("2", "y"), ("4", "z")],
            "gamma": [("5", "p"), ("6", "q")],
        }
        super().setUpClass()

    def test_right_outer_join_basic_set(self):
        instring = "alpha \\right_outer_join_{a1 = b1} beta;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "1", "x"),
            ("2", "b", "2", "y"),
            (None, None, "4", "z"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_right_outer_join_basic_bag(self):
        instring = "alpha \\right_outer_join_{a1 = b1} beta;"
        translation = self.translate_bag(instring)
        expected = [
            ("1", "a", "1", "x"),
            ("2", "b", "2", "y"),
            (None, None, "4", "z"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_right_outer_join_complex_condition_set(self):
        instring = "alpha \\right_outer_join_{alpha.a1 = beta.b1 and a2 = 'a'} beta;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "1", "x"),
            (None, None, "2", "y"),
            (None, None, "4", "z"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_right_outer_join_with_project_set(self):
        instring = (
            "\\project_{alpha.a1, beta.b1} (alpha \\right_outer_join_{a1 = b1} beta);"
        )
        translation = self.translate_set(instring)
        expected = [
            ("1", "1"),
            ("2", "2"),
            (None, "4"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_right_outer_join_with_select_set(self):
        instring = "\\select_{beta.b1 > '1'} (alpha \\right_outer_join_{a1 = b1} beta);"
        translation = self.translate_set(instring)
        expected = [
            ("2", "b", "2", "y"),
            (None, None, "4", "z"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_right_outer_join_chained_set(self):
        instring = "(alpha \\right_outer_join_{a1 = b1} beta) \\join gamma;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "1", "x", "5", "p"),
            ("1", "a", "1", "x", "6", "q"),
            ("2", "b", "2", "y", "5", "p"),
            ("2", "b", "2", "y", "6", "q"),
            (None, None, "4", "z", "5", "p"),
            (None, None, "4", "z", "6", "q"),
        ]
        self.assertCountEqual(expected, self.query_list(translation))


class TestDefined(TestTranslator):
    @classmethod
    def setUpClass(cls):
        cls.schema = {
            "alpha": ["a1", "a2", "a3"],
            "beta": ["b1", "b2"],
        }
        cls.data = {
            "alpha": [
                ("1", "a", "x"),  # All non-null
                ("2", None, "y"),  # a2 is null
                (None, "c", "z"),  # a1 is null
                ("4", "d", None),  # a3 is null
                (None, None, None),  # All null
            ],
            "beta": [
                ("1", "p"),  # All non-null
                (None, "q"),  # b1 is null
                ("3", None),  # b2 is null
            ],
        }
        super().setUpClass()

    def test_defined_single_attribute_set(self):
        instring = "\\select_{defined(a1)} alpha;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "x"),  # a1 = "1" (defined)
            ("2", None, "y"),  # a1 = "2" (defined)
            ("4", "d", None),  # a1 = "4" (defined)
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_defined_single_attribute_bag(self):
        instring = "\\select_{defined(a1)} alpha;"
        translation = self.translate_bag(instring)
        expected = [
            ("1", "a", "x"),  # a1 = "1" (defined)
            ("2", None, "y"),  # a1 = "2" (defined)
            ("4", "d", None),  # a1 = "4" (defined)
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_not_defined_single_attribute_set(self):
        instring = "\\select_{not defined(a1)} alpha;"
        translation = self.translate_set(instring)
        expected = [
            (None, "c", "z"),  # a1 is null
            (None, None, None),  # a1 is null
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_defined_multiple_attributes_set(self):
        instring = "\\select_{defined(a1) and defined(a2)} alpha;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "x"),  # Both a1 and a2 defined
            ("4", "d", None),  # Both a1 and a2 defined (a3 is null but that's OK)
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_defined_or_defined_set(self):
        instring = "\\select_{defined(a1) or defined(a2)} alpha;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "x"),  # Both defined
            ("2", None, "y"),  # a1 defined, a2 null
            (None, "c", "z"),  # a1 null, a2 defined
            ("4", "d", None),  # a1 defined, a2 defined
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_defined_with_equality_set(self):
        instring = "\\select_{defined(a1) and a1 = '1'} alpha;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "x"),  # a1 defined and equals "1"
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_not_defined_with_equality_set(self):
        instring = "\\select_{not defined(a1) or a2 = 'c'} alpha;"
        translation = self.translate_set(instring)
        expected = [
            (None, "c", "z"),  # a1 not defined, a2 = "c"
            (None, None, None),  # a1 not defined
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_complex_defined_condition_set(self):
        instring = "\\select_{defined(a1) and (a2 = 'a' or not defined(a3))} alpha;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "x"),  # a1 defined, a2 = "a"
            ("4", "d", None),  # a1 defined, a3 not defined
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_defined_with_relation_attribute_set(self):
        instring = "\\select_{defined(alpha.a1)} alpha;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "x"),  # alpha.a1 defined
            ("2", None, "y"),  # alpha.a1 defined
            ("4", "d", None),  # alpha.a1 defined
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_defined_with_project_set(self):
        instring = "\\project_{a1, a2} \\select_{defined(a1)} alpha;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a"),  # a1 defined
            ("2", None),  # a1 defined
            ("4", "d"),  # a1 defined
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_defined_in_join_condition_set(self):
        instring = "alpha \\join_{defined(alpha.a1) and defined(beta.b1)} beta;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "x", "1", "p"),  # Both a1 and b1 defined
            ("2", None, "y", "1", "p"),  # Both a1 and b1 defined
            ("4", "d", None, "1", "p"),  # Both a1 and b1 defined
            ("1", "a", "x", "3", None),  # Both a1 and b1 defined (b1="3")
            ("2", None, "y", "3", None),  # Both a1 and b1 defined (b1="3")
            ("4", "d", None, "3", None),  # Both a1 and b1 defined (b1="3")
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_defined_with_outer_join_set(self):
        instring = (
            "alpha \\left_outer_join_{defined(alpha.a1) and defined(beta.b1)} beta;"
        )
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "x", "1", "p"),  # Both defined - matches
            ("2", None, "y", "1", "p"),  # Both defined - matches
            ("4", "d", None, "1", "p"),  # Both defined - matches
            ("1", "a", "x", "3", None),  # Both defined - matches (b1="3")
            ("2", None, "y", "3", None),  # Both defined - matches (b1="3")
            ("4", "d", None, "3", None),  # Both defined - matches (b1="3")
            (None, "c", "z", None, None),  # a1 not defined - no match
            (None, None, None, None, None),  # a1 not defined - no match
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_defined_with_union_set(self):
        instring = "\\select_{defined(a1)} alpha \\union \\select_{defined(a1)} alpha;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "x"),  # From alpha where a1 defined
            ("2", None, "y"),  # From alpha where a1 defined
            ("4", "d", None),  # From alpha where a1 defined
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_multiple_defined_conditions_set(self):
        instring = "\\select_{defined(a1)} \\select_{defined(a2)} alpha;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "x"),  # Both a1 and a2 defined
            ("4", "d", None),  # Both a1 and a2 defined (a3 is null)
        ]
        self.assertCountEqual(expected, self.query_list(translation))

    def test_defined_with_assign_set(self):
        instring = "defined_alpha := \\select_{defined(a1)} alpha; defined_alpha;"
        translation = self.translate_set(instring)
        expected = [
            ("1", "a", "x"),  # a1 defined
            ("2", None, "y"),  # a1 defined
            ("4", "d", None),  # a1 defined
        ]
        self.assertCountEqual(expected, self.query_list(translation))
