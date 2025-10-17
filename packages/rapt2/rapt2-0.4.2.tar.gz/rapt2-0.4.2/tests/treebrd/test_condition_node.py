from unittest import TestCase

from rapt2.treebrd.condition_node import (BinaryConditionalOperator,
                                          BinaryConditionNode,
                                          IdentityConditionNode,
                                          UnaryConditionalOperator,
                                          UnaryConditionNode)
from rapt2.treebrd.schema import Schema
from rapt2.transformers.qtree.qtree_translator import QTreeTranslator as QTreeTranslator
from rapt2.transformers.sql.sql_translator import SQLTranslator as SQLTranslator


class ConditionNodeTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        self.schema = Schema(
            {
                "alpha": ["a1"],
                "beta": ["b1", "b2"],
                "gamma": ["c1", "c2", "c3"],
            }
        )
        self.qtree_translator = QTreeTranslator()
        self.sql_translator = SQLTranslator()


class TestConditionNode(ConditionNodeTestCase):
    def test_identity_condition_node(self):
        node = IdentityConditionNode("alpha.a1")
        self.assertEqual(self.qtree_translator.translate_condition(node), "alpha.a1")
        self.assertEqual(self.sql_translator.translate_condition(node), "alpha.a1")
        self.assertEqual(node.attribute_references(), ["alpha.a1"])

    def test_unary_condition_node(self):
        child = IdentityConditionNode("alpha.a1")
        node = UnaryConditionNode(UnaryConditionalOperator.NOT, child)
        self.assertEqual(self.qtree_translator.translate_condition(node), "\\neg alpha.a1")
        self.assertEqual(self.sql_translator.translate_condition(node), "NOT alpha.a1")
        self.assertEqual(node.attribute_references(), ["alpha.a1"])

    def test_binary_condition_node(self):
        left = IdentityConditionNode("alpha.a1")
        right = IdentityConditionNode("beta.b1")
        node = BinaryConditionNode(BinaryConditionalOperator.AND, left, right)
        self.assertEqual(self.qtree_translator.translate_condition(node), "(alpha.a1 \\land beta.b1)")
        self.assertEqual(self.sql_translator.translate_condition(node), "(alpha.a1 AND beta.b1)")
        self.assertEqual(node.attribute_references(), ["alpha.a1", "beta.b1"])
