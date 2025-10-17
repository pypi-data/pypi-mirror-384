from rapt2.treebrd.condition_node import (BinaryConditionalOperator,
                                          BinaryConditionNode,
                                          IdentityConditionNode)
from rapt2.treebrd.errors import AttributeReferenceError, InputError
from rapt2.treebrd.node import (BinaryNode, CrossJoinNode, DifferenceNode,
                                FullOuterJoinNode, IntersectNode,
                                LeftOuterJoinNode, Operator,
                                RightOuterJoinNode, ThetaJoinNode, UnionNode)
from tests.treebrd.test_node import NodeTestCase


class BinaryTestCase(NodeTestCase):
    pass


class TestBinaryNode(BinaryTestCase):
    def test_binary_children(self):
        node = BinaryNode(Operator.union, self.beta, self.gamma)
        self.assertEqual(self.beta, node.left)
        self.assertEqual(self.gamma, node.right)


class TestBinaryNodeEquality(BinaryTestCase):
    def test_equality_when_identical(self):
        node = BinaryNode(Operator.cross_join, self.alpha, self.beta, "borg")
        same = node
        self.assertTrue(node == same)

    def test_equality_when_same_operator_and_name(self):
        node = BinaryNode(Operator.cross_join, self.alpha, self.beta, "borg")
        twin = BinaryNode(Operator.cross_join, self.alpha, self.beta, "borg")
        self.assertTrue(node == twin)

    def test_non_equality_when_different_operator_and_name(self):
        node = BinaryNode(Operator.natural_join, self.alpha, self.beta, "borg")
        other = BinaryNode(Operator.cross_join, self.alpha, self.beta, "other")
        self.assertTrue(node != other)

    def test_non_equality_when_different_operator(self):
        node = BinaryNode(Operator.natural_join, self.alpha, self.beta, "borg")
        other = BinaryNode(Operator.cross_join, self.alpha, self.beta, "borg")
        self.assertTrue(node != other)

    def test_non_equality_when_different_name(self):
        node = BinaryNode(Operator.cross_join, self.alpha, self.beta, "borg")
        other = BinaryNode(Operator.cross_join, self.alpha, self.beta, "other")
        self.assertTrue(node != other)

    def test_non_equality_when_same_operator_and_one_no_name(self):
        node = BinaryNode(Operator.cross_join, self.alpha, self.beta, "borg")
        other = BinaryNode(Operator.cross_join, self.alpha, self.beta)
        self.assertTrue(node != other)


class TestUnionNode(BinaryTestCase):
    def test_operator_on_init(self):
        node = UnionNode(self.beta, self.beta)
        self.assertEqual(Operator.union, node.operator)

    def test_children_on_init(self):
        node = UnionNode(self.twin, self.twin_prime)
        self.assertEqual(self.twin, node.left)
        self.assertEqual(self.twin_prime, node.right)

    def test_attributes(self):
        node = UnionNode(self.beta, self.beta)
        expected = get_attributes("beta", self.schema)
        self.assertEqual(expected, node.attributes.to_list())

    def test_mismatch(self):
        self.assertRaises(InputError, UnionNode, self.beta, self.gamma)


class TestDifferenceNode(BinaryTestCase):
    def test_operator_on_init(self):
        node = DifferenceNode(self.beta, self.beta)
        self.assertEqual(Operator.difference, node.operator)

    def test_name_on_init(self):
        node = DifferenceNode(self.beta, self.beta)
        self.assertIsNone(node.name)

    def test_children_on_init(self):
        node = DifferenceNode(self.twin, self.twin_prime)
        self.assertEqual(self.twin, node.left)
        self.assertEqual(self.twin_prime, node.right)

    def test_attributes(self):
        node = DifferenceNode(self.beta, self.beta)
        expected = get_attributes("beta", self.schema)
        self.assertEqual(expected, node.attributes.to_list())

    def test_mismatch(self):
        self.assertRaises(InputError, DifferenceNode, self.beta, self.gamma)


class TestIntersectionNode(BinaryTestCase):
    def test_operator_on_init(self):
        node = IntersectNode(self.beta, self.beta)
        self.assertEqual(Operator.intersect, node.operator)

    def test_children_on_init(self):
        node = IntersectNode(self.twin, self.twin_prime)
        self.assertEqual(self.twin, node.left)
        self.assertEqual(self.twin_prime, node.right)

    def test_attributes(self):
        node = IntersectNode(self.beta, self.beta)
        expected = get_attributes("beta", self.schema)
        self.assertEqual(expected, node.attributes.to_list())

    def test_mismatch(self):
        self.assertRaises(InputError, IntersectNode, self.beta, self.gamma)


class TestJoinNode(BinaryTestCase):
    def test_operator_on_init(self):
        node = CrossJoinNode(self.alpha, self.beta)
        self.assertEqual(Operator.cross_join, node.operator)

    def test_children_on_init(self):
        node = CrossJoinNode(self.beta, self.gamma)
        self.assertEqual(self.beta, node.left)
        self.assertEqual(self.gamma, node.right)

    def test_attributes_on_init(self):
        node = CrossJoinNode(self.beta, self.gamma)
        expected = get_attributes(
            "beta", self.schema, use_prefix=True
        ) + get_attributes("gamma", self.schema, use_prefix=True)
        self.assertEqual(expected, node.attributes.to_list())

    def test_attributes_when_left_child_is_join(self):
        left = CrossJoinNode(self.beta, self.gamma)
        node = CrossJoinNode(left, self.alpha)
        expected = (
            get_attributes("beta", self.schema, use_prefix=True)
            + get_attributes("gamma", self.schema, use_prefix=True)
            + get_attributes("alpha", self.schema, use_prefix=True)
        )
        self.assertEqual(expected, node.attributes.to_list())

    def test_attributes_when_right_child_is_join(self):
        right = CrossJoinNode(self.gamma, self.alpha)
        node = CrossJoinNode(self.beta, right)
        expected = (
            get_attributes("beta", self.schema, use_prefix=True)
            + get_attributes("gamma", self.schema, use_prefix=True)
            + get_attributes("alpha", self.schema, use_prefix=True)
        )
        self.assertEqual(expected, node.attributes.to_list())

    def test_attributes_when_both_children_are_join(self):
        left = CrossJoinNode(self.alpha, self.beta)
        right = CrossJoinNode(self.gamma, self.twin)
        node = CrossJoinNode(left, right)
        expected = (
            get_attributes("alpha", self.schema, use_prefix=True)
            + get_attributes("beta", self.schema, use_prefix=True)
            + get_attributes("gamma", self.schema, use_prefix=True)
            + get_attributes("twin", self.schema, use_prefix=True)
        )
        self.assertEqual(expected, node.attributes.to_list())


class TestCrossNode(BinaryTestCase):
    def test_operator_on_init(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.EQUAL,
            IdentityConditionNode("a1"),
            IdentityConditionNode("b1"),
        )
        node = ThetaJoinNode(self.alpha, self.beta, condition)
        self.assertEqual(Operator.theta_join, node.operator)

    def test_children_on_init(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.EQUAL,
            IdentityConditionNode("a1"),
            IdentityConditionNode("b1"),
        )
        node = ThetaJoinNode(self.alpha, self.beta, condition)
        self.assertEqual(self.alpha, node.left)
        self.assertEqual(self.beta, node.right)

    def test_attributes_on_init(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.EQUAL,
            IdentityConditionNode("a1"),
            IdentityConditionNode("b1"),
        )
        node = ThetaJoinNode(self.alpha, self.beta, condition)
        expected = get_attributes(
            "alpha", self.schema, use_prefix=True
        ) + get_attributes("beta", self.schema, use_prefix=True)
        self.assertEqual(expected, node.attributes.to_list())

    def test_condition_when_init_has_condition(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.EQUAL,
            IdentityConditionNode("a1"),
            IdentityConditionNode("b1"),
        )
        actual = ThetaJoinNode(self.alpha, self.beta, condition).conditions
        self.assertEqual(condition, actual)

    def test_condition_when_multiple_conditions(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.AND,
            BinaryConditionNode(
                BinaryConditionalOperator.GREATER_THAN,
                IdentityConditionNode("a1"),
                IdentityConditionNode("41"),
            ),
            BinaryConditionNode(
                BinaryConditionalOperator.LESS_THAN,
                IdentityConditionNode("b1"),
                IdentityConditionNode("43"),
            ),
        )
        actual = ThetaJoinNode(self.alpha, self.beta, condition).conditions
        self.assertEqual(condition, actual)

    def test_condition_when_with_prefix(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.GREATER_THAN,
            IdentityConditionNode("alpha.a1"),
            IdentityConditionNode("41"),
        )
        actual = ThetaJoinNode(self.alpha, self.beta, condition).conditions
        self.assertEqual(condition, actual)

    def test_condition_when_multiple_conditions_with_prefix(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.AND,
            BinaryConditionNode(
                BinaryConditionalOperator.GREATER_THAN,
                IdentityConditionNode("alpha.a1"),
                IdentityConditionNode("41"),
            ),
            BinaryConditionNode(
                BinaryConditionalOperator.LESS_THAN,
                IdentityConditionNode("beta.b1"),
                IdentityConditionNode("43"),
            ),
        )
        actual = ThetaJoinNode(self.alpha, self.beta, condition).conditions
        self.assertEqual(condition, actual)

    def test_exception_when_first_attribute_in_condition_is_wrong(self):
        self.assertRaises(
            AttributeReferenceError,
            ThetaJoinNode,
            self.alpha,
            self.beta,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("a2"),
                IdentityConditionNode("42"),
            ),
        )

    def test_exception_when_second_attribute_in_condition_is_wrong(self):
        self.assertRaises(
            AttributeReferenceError,
            ThetaJoinNode,
            self.alpha,
            self.beta,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("a2"),
                IdentityConditionNode("a2"),
            ),
        )

    def test_exception_when_both_attributes_in_condition_are_wrong(self):
        self.assertRaises(
            AttributeReferenceError,
            ThetaJoinNode,
            self.alpha,
            self.beta,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("a2"),
                IdentityConditionNode("a3"),
            ),
        )

    def test_exception_when_prefix_in_condition_is_wrong(self):
        self.assertRaises(
            AttributeReferenceError,
            ThetaJoinNode,
            self.alpha,
            self.beta,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("beta.a1"),
                IdentityConditionNode("42"),
            ),
        )

    def test_exception_when_ambiguous_attributes(self):
        self.assertRaises(
            AttributeReferenceError,
            ThetaJoinNode,
            self.alpha,
            self.ambiguous,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("d1"),
                IdentityConditionNode("42"),
            ),
        )


class TestFullOuterJoinNode(BinaryTestCase):
    def test_operator_on_init(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.EQUAL,
            IdentityConditionNode("a1"),
            IdentityConditionNode("b1"),
        )
        node = FullOuterJoinNode(self.alpha, self.beta, condition)
        self.assertEqual(Operator.full_outer_join, node.operator)

    def test_children_on_init(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.EQUAL,
            IdentityConditionNode("a1"),
            IdentityConditionNode("b1"),
        )
        node = FullOuterJoinNode(self.alpha, self.beta, condition)
        self.assertEqual(self.alpha, node.left)
        self.assertEqual(self.beta, node.right)

    def test_attributes_on_init(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.EQUAL,
            IdentityConditionNode("a1"),
            IdentityConditionNode("b1"),
        )
        node = FullOuterJoinNode(self.alpha, self.beta, condition)
        expected = get_attributes(
            "alpha", self.schema, use_prefix=True
        ) + get_attributes("beta", self.schema, use_prefix=True)
        self.assertEqual(expected, node.attributes.to_list())

    def test_condition_when_init_has_condition(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.EQUAL,
            IdentityConditionNode("a1"),
            IdentityConditionNode("b1"),
        )
        actual = FullOuterJoinNode(self.alpha, self.beta, condition).conditions
        self.assertEqual(condition, actual)

    def test_condition_when_multiple_conditions(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.AND,
            BinaryConditionNode(
                BinaryConditionalOperator.GREATER_THAN,
                IdentityConditionNode("a1"),
                IdentityConditionNode("41"),
            ),
            BinaryConditionNode(
                BinaryConditionalOperator.LESS_THAN,
                IdentityConditionNode("b1"),
                IdentityConditionNode("43"),
            ),
        )
        actual = FullOuterJoinNode(self.alpha, self.beta, condition).conditions
        self.assertEqual(condition, actual)

    def test_condition_when_with_prefix(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.GREATER_THAN,
            IdentityConditionNode("alpha.a1"),
            IdentityConditionNode("41"),
        )
        actual = FullOuterJoinNode(self.alpha, self.beta, condition).conditions
        self.assertEqual(condition, actual)

    def test_condition_when_multiple_conditions_with_prefix(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.AND,
            BinaryConditionNode(
                BinaryConditionalOperator.GREATER_THAN,
                IdentityConditionNode("alpha.a1"),
                IdentityConditionNode("41"),
            ),
            BinaryConditionNode(
                BinaryConditionalOperator.LESS_THAN,
                IdentityConditionNode("beta.b1"),
                IdentityConditionNode("43"),
            ),
        )
        actual = FullOuterJoinNode(self.alpha, self.beta, condition).conditions
        self.assertEqual(condition, actual)

    def test_exception_when_first_attribute_in_condition_is_wrong(self):
        self.assertRaises(
            AttributeReferenceError,
            FullOuterJoinNode,
            self.alpha,
            self.beta,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("a2"),
                IdentityConditionNode("42"),
            ),
        )

    def test_exception_when_second_attribute_in_condition_is_wrong(self):
        self.assertRaises(
            AttributeReferenceError,
            FullOuterJoinNode,
            self.alpha,
            self.beta,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("a2"),
                IdentityConditionNode("a2"),
            ),
        )

    def test_exception_when_both_attributes_in_condition_are_wrong(self):
        self.assertRaises(
            AttributeReferenceError,
            FullOuterJoinNode,
            self.alpha,
            self.beta,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("a2"),
                IdentityConditionNode("a3"),
            ),
        )

    def test_exception_when_prefix_in_condition_is_wrong(self):
        self.assertRaises(
            AttributeReferenceError,
            FullOuterJoinNode,
            self.alpha,
            self.beta,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("beta.a1"),
                IdentityConditionNode("42"),
            ),
        )

    def test_exception_when_ambiguous_attributes(self):
        self.assertRaises(
            AttributeReferenceError,
            FullOuterJoinNode,
            self.alpha,
            self.ambiguous,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("d1"),
                IdentityConditionNode("42"),
            ),
        )


class TestLeftOuterJoinNode(BinaryTestCase):
    def test_operator_on_init(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.EQUAL,
            IdentityConditionNode("a1"),
            IdentityConditionNode("b1"),
        )
        node = LeftOuterJoinNode(self.alpha, self.beta, condition)
        self.assertEqual(Operator.left_outer_join, node.operator)

    def test_children_on_init(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.EQUAL,
            IdentityConditionNode("a1"),
            IdentityConditionNode("b1"),
        )
        node = LeftOuterJoinNode(self.alpha, self.beta, condition)
        self.assertEqual(self.alpha, node.left)
        self.assertEqual(self.beta, node.right)

    def test_attributes_on_init(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.EQUAL,
            IdentityConditionNode("a1"),
            IdentityConditionNode("b1"),
        )
        node = LeftOuterJoinNode(self.alpha, self.beta, condition)
        expected = get_attributes(
            "alpha", self.schema, use_prefix=True
        ) + get_attributes("beta", self.schema, use_prefix=True)
        self.assertEqual(expected, node.attributes.to_list())

    def test_condition_when_init_has_condition(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.EQUAL,
            IdentityConditionNode("a1"),
            IdentityConditionNode("b1"),
        )
        actual = LeftOuterJoinNode(self.alpha, self.beta, condition).conditions
        self.assertEqual(condition, actual)

    def test_condition_when_multiple_conditions(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.AND,
            BinaryConditionNode(
                BinaryConditionalOperator.GREATER_THAN,
                IdentityConditionNode("a1"),
                IdentityConditionNode("41"),
            ),
            BinaryConditionNode(
                BinaryConditionalOperator.LESS_THAN,
                IdentityConditionNode("b1"),
                IdentityConditionNode("43"),
            ),
        )
        actual = LeftOuterJoinNode(self.alpha, self.beta, condition).conditions
        self.assertEqual(condition, actual)

    def test_condition_when_with_prefix(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.GREATER_THAN,
            IdentityConditionNode("alpha.a1"),
            IdentityConditionNode("41"),
        )
        actual = LeftOuterJoinNode(self.alpha, self.beta, condition).conditions
        self.assertEqual(condition, actual)

    def test_condition_when_multiple_conditions_with_prefix(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.AND,
            BinaryConditionNode(
                BinaryConditionalOperator.GREATER_THAN,
                IdentityConditionNode("alpha.a1"),
                IdentityConditionNode("41"),
            ),
            BinaryConditionNode(
                BinaryConditionalOperator.LESS_THAN,
                IdentityConditionNode("beta.b1"),
                IdentityConditionNode("43"),
            ),
        )
        actual = LeftOuterJoinNode(self.alpha, self.beta, condition).conditions
        self.assertEqual(condition, actual)

    def test_exception_when_first_attribute_in_condition_is_wrong(self):
        self.assertRaises(
            AttributeReferenceError,
            LeftOuterJoinNode,
            self.alpha,
            self.beta,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("a2"),
                IdentityConditionNode("42"),
            ),
        )

    def test_exception_when_second_attribute_in_condition_is_wrong(self):
        self.assertRaises(
            AttributeReferenceError,
            LeftOuterJoinNode,
            self.alpha,
            self.beta,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("a2"),
                IdentityConditionNode("a2"),
            ),
        )

    def test_exception_when_both_attributes_in_condition_are_wrong(self):
        self.assertRaises(
            AttributeReferenceError,
            LeftOuterJoinNode,
            self.alpha,
            self.beta,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("a2"),
                IdentityConditionNode("a3"),
            ),
        )

    def test_exception_when_prefix_in_condition_is_wrong(self):
        self.assertRaises(
            AttributeReferenceError,
            LeftOuterJoinNode,
            self.alpha,
            self.beta,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("beta.a1"),
                IdentityConditionNode("42"),
            ),
        )

    def test_exception_when_ambiguous_attributes(self):
        self.assertRaises(
            AttributeReferenceError,
            LeftOuterJoinNode,
            self.alpha,
            self.ambiguous,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("d1"),
                IdentityConditionNode("42"),
            ),
        )


class TestRightOuterJoinNode(BinaryTestCase):
    def test_operator_on_init(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.EQUAL,
            IdentityConditionNode("a1"),
            IdentityConditionNode("b1"),
        )
        node = RightOuterJoinNode(self.alpha, self.beta, condition)
        self.assertEqual(Operator.right_outer_join, node.operator)

    def test_children_on_init(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.EQUAL,
            IdentityConditionNode("a1"),
            IdentityConditionNode("b1"),
        )
        node = RightOuterJoinNode(self.alpha, self.beta, condition)
        self.assertEqual(self.alpha, node.left)
        self.assertEqual(self.beta, node.right)

    def test_attributes_on_init(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.EQUAL,
            IdentityConditionNode("a1"),
            IdentityConditionNode("b1"),
        )
        node = RightOuterJoinNode(self.alpha, self.beta, condition)
        expected = get_attributes(
            "alpha", self.schema, use_prefix=True
        ) + get_attributes("beta", self.schema, use_prefix=True)
        self.assertEqual(expected, node.attributes.to_list())

    def test_condition_when_init_has_condition(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.EQUAL,
            IdentityConditionNode("a1"),
            IdentityConditionNode("b1"),
        )
        actual = RightOuterJoinNode(self.alpha, self.beta, condition).conditions
        self.assertEqual(condition, actual)

    def test_condition_when_multiple_conditions(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.AND,
            BinaryConditionNode(
                BinaryConditionalOperator.GREATER_THAN,
                IdentityConditionNode("a1"),
                IdentityConditionNode("41"),
            ),
            BinaryConditionNode(
                BinaryConditionalOperator.LESS_THAN,
                IdentityConditionNode("b1"),
                IdentityConditionNode("43"),
            ),
        )
        actual = RightOuterJoinNode(self.alpha, self.beta, condition).conditions
        self.assertEqual(condition, actual)

    def test_condition_when_with_prefix(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.GREATER_THAN,
            IdentityConditionNode("alpha.a1"),
            IdentityConditionNode("41"),
        )
        actual = RightOuterJoinNode(self.alpha, self.beta, condition).conditions
        self.assertEqual(condition, actual)

    def test_condition_when_multiple_conditions_with_prefix(self):
        condition = BinaryConditionNode(
            BinaryConditionalOperator.AND,
            BinaryConditionNode(
                BinaryConditionalOperator.GREATER_THAN,
                IdentityConditionNode("alpha.a1"),
                IdentityConditionNode("41"),
            ),
            BinaryConditionNode(
                BinaryConditionalOperator.LESS_THAN,
                IdentityConditionNode("beta.b1"),
                IdentityConditionNode("43"),
            ),
        )
        actual = RightOuterJoinNode(self.alpha, self.beta, condition).conditions
        self.assertEqual(condition, actual)

    def test_exception_when_first_attribute_in_condition_is_wrong(self):
        self.assertRaises(
            AttributeReferenceError,
            RightOuterJoinNode,
            self.alpha,
            self.beta,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("a2"),
                IdentityConditionNode("42"),
            ),
        )

    def test_exception_when_second_attribute_in_condition_is_wrong(self):
        self.assertRaises(
            AttributeReferenceError,
            RightOuterJoinNode,
            self.alpha,
            self.beta,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("a2"),
                IdentityConditionNode("a2"),
            ),
        )

    def test_exception_when_both_attributes_in_condition_are_wrong(self):
        self.assertRaises(
            AttributeReferenceError,
            RightOuterJoinNode,
            self.alpha,
            self.beta,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("a2"),
                IdentityConditionNode("a3"),
            ),
        )

    def test_exception_when_prefix_in_condition_is_wrong(self):
        self.assertRaises(
            AttributeReferenceError,
            RightOuterJoinNode,
            self.alpha,
            self.beta,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("beta.a1"),
                IdentityConditionNode("42"),
            ),
        )

    def test_exception_when_ambiguous_attributes(self):
        self.assertRaises(
            AttributeReferenceError,
            RightOuterJoinNode,
            self.alpha,
            self.ambiguous,
            BinaryConditionNode(
                BinaryConditionalOperator.EQUAL,
                IdentityConditionNode("d1"),
                IdentityConditionNode("42"),
            ),
        )


def get_attributes(name, schema, use_prefix=False):
    def prefixed(attribute):
        if use_prefix:
            return "{name}.{attr}".format(name=name, attr=attribute)
        else:
            return attribute

    return [prefixed(attribute) for attribute in schema.get_attributes(name)]
