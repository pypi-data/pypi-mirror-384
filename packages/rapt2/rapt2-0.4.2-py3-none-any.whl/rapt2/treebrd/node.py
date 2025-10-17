import copy
from enum import Enum, auto

from .attributes import AttributeList
from .condition_node import ConditionNode
from .errors import InputError, RelationReferenceError


class Node:
    """
    A Node from a relational algebra parse tree.

    A node represents three intermingled concepts:
        - A relational algebra operator and the parameters requires
        - Together with its children, a single relational algebra expression
        - A method of mutating a collection of tuples
    """

    name: str | None

    def __init__(self, operator, name=None):
        """
        Construct a node.
        :param name: The name of the relation.
        :param operator: The operator used to create this relation. One of
        the node.Operator enum.
        """
        self.operator = operator
        self.name = name
        self.attributes = None

    def __eq__(self, other):
        """
        Return true if other is a node with the same operator, name and
        attributes. Else return false.
        :param other: A Node.
        :return: True if other is equivalent to this node.
        """
        if type(self) is not type(other):
            return False
        if self.name != other.name:
            return False
        if self.operator != other.operator:
            return False
        if self.attributes != other.attributes:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)


class RelationNode(Node):
    """
    A relation.
    """

    def __init__(self, name: str, schema):
        super().__init__(Operator.relation, name)
        self.attributes = AttributeList(schema.get_attributes(name), name)

    def post_order(self):
        return [self]


class DefinitionNode(Node):
    """
    A relation definition.
    """

    def __init__(self, name: str, attributes: list, schema):
        super().__init__(Operator.definition, name)
        self.attributes = AttributeList(attributes, name)
        schema.add(name, self.attributes.names)

    def post_order(self):
        return [self]


class UnaryNode(Node):
    """
    A Node with one child.
    """

    def __init__(self, operator, child, name: str | None = None):
        super().__init__(operator, name)
        self.child = child

        if not name:
            self.name = self.child.name

        self.attributes = copy.copy(child.attributes)

    def __eq__(self, other):
        return super().__eq__(other) and self.child.__eq__(other.child)

    def post_order(self):
        return self.child.post_order() + [self]


class SelectNode(UnaryNode):
    """
    A relation that results from the relation algebra select operator.
    """

    def __init__(self, child, conditions: ConditionNode):
        super().__init__(Operator.select, child)
        self.attributes.validate(conditions.attribute_references())
        self.conditions = conditions

    def __eq__(self, other):
        return self.conditions == other.conditions and super().__eq__(other)


class ProjectNode(UnaryNode):
    """
    A relation that results from the relation algebra project operator.
    """

    def __init__(self, child, attributes):
        super().__init__(Operator.project, child=child)
        self.attributes.trim(attributes)


class RenameNode(UnaryNode):
    """
    A relation that results from the relation algebra rename operator.
    """

    def __init__(self, child, name, attributes, schema):
        """
        Construct a RenameNode.
        :param name: The new name for the relation.
        :param attributes: A list of new names for every attribute or an empty
        list.
        :param child: The child of this Node.
        """
        super().__init__(Operator.rename, child, name)
        if schema.contains(name):
            raise RelationReferenceError(
                "Relation '{name}' already exists.".format(name=name)
            )
        self.attributes.rename(attributes, self.name)


class AssignNode(UnaryNode):
    """
    A relation that results from the relation algebra assign operator.
    """

    def __init__(self, child, name, attributes, schema):
        """
        Construct an AssignNode.
        :param name: The new name for the relation.
        :param attributes: A list of new names for every attribute or an empty
        list.
        :param child: The child of this Node.
        """
        if not name:
            raise InputError("Name is required for assignment.")

        if attributes and len(attributes) != len(child.attributes):
            raise InputError("Assignment requires naming all attributes.")

        super().__init__(Operator.assign, child, name)
        self.attributes.rename(attributes, name)
        schema.add(name, self.attributes.names)


class BinaryNode(Node):
    """
    A Node with two children, a left and a right.
    """

    def __init__(self, operator, left, right, name=None):
        super().__init__(operator, name)
        self.left = left
        self.right = right

    def __eq__(self, other):
        return (
            super().__eq__(other)
            and self.left.__eq__(other.left)
            and self.right.__eq__(other.right)
        )

    def post_order(self):
        return self.left.post_order() + self.right.post_order() + [self]


class JoinNode(BinaryNode):
    """
    A relation that results from the relation algebra cross join operator.
    """

    def __init__(self, operator, left, right):
        if left.name and right.name and left.name == right.name:
            raise RelationReferenceError("Ambiguous relation reference.")
        super().__init__(operator, left, right, None)
        self.attributes = AttributeList.merge(left.attributes, right.attributes)


class CrossJoinNode(JoinNode):
    """
    A relation that results from the relation algebra cross join operator.
    """

    def __init__(self, left, right):
        super().__init__(Operator.cross_join, left, right)


class NaturalJoinNode(JoinNode):
    """
    A relation that results from the relation algebra natural join operator.
    """

    def __init__(self, left, right):
        super().__init__(Operator.natural_join, left, right)
        left_attributes = [attribute.prefixed for attribute in self.left.attributes]
        left_names = self.left.attributes.names
        right_attributes = [
            attribute.prefixed
            for attribute in self.right.attributes
            if attribute.name not in left_names
        ]
        self.attributes.trim(left_attributes + right_attributes)


class ThetaJoinNode(JoinNode):
    """
    A relation that results from the relation algebra theta join operator.
    """

    def __init__(self, left, right, conditions: ConditionNode):
        super().__init__(Operator.theta_join, left, right)
        self.attributes.validate(conditions.attribute_references())
        self.conditions = conditions

    def __eq__(self, other):
        return self.conditions == other.conditions and super().__eq__(other)


class FullOuterJoinNode(JoinNode):
    """
    A relation that results from the relation algebra full outer join operator.
    """

    def __init__(self, left, right, conditions: ConditionNode):
        super().__init__(Operator.full_outer_join, left, right)
        self.attributes.validate(conditions.attribute_references())
        self.conditions = conditions

    def __eq__(self, other):
        return self.conditions == other.conditions and super().__eq__(other)


class LeftOuterJoinNode(JoinNode):
    """
    A relation that results from the relation algebra left outer join operator.
    """

    def __init__(self, left, right, conditions: ConditionNode):
        super().__init__(Operator.left_outer_join, left, right)
        self.attributes.validate(conditions.attribute_references())
        self.conditions = conditions

    def __eq__(self, other):
        return self.conditions == other.conditions and super().__eq__(other)


class RightOuterJoinNode(JoinNode):
    """
    A relation that results from the relation algebra right outer join operator.
    """

    def __init__(self, left, right, conditions: ConditionNode):
        super().__init__(Operator.right_outer_join, left, right)
        self.attributes.validate(conditions.attribute_references())
        self.conditions = conditions

    def __eq__(self, other):
        return self.conditions == other.conditions and super().__eq__(other)


class SetOperatorNode(BinaryNode):
    """
    An abstract class for binary nodes with set operators.
    """

    def __init__(self, operator, left, right):
        super().__init__(operator, left, right, None)

        names = left.attributes.names
        if not names == right.attributes.names:
            raise InputError("Set operations require identical relation schemas.")

        self.attributes = AttributeList(names, None)


class UnionNode(SetOperatorNode):
    """
    A relation that results from the relation algebra union operator.
    """

    def __init__(self, left, right):
        super().__init__(Operator.union, left, right)


class DifferenceNode(SetOperatorNode):
    """
    A relation that results from the relation algebra difference operator.
    """

    def __init__(self, left, right):
        super().__init__(Operator.difference, left, right)


class IntersectNode(SetOperatorNode):
    """
    A relation that results from the relation algebra intersect operator.
    """

    def __init__(self, left, right):
        super().__init__(Operator.intersect, left, right)


class DependencyNode(Node):
    """
    Base class for dependency nodes.
    """

    def __init__(self, operator, relation_name, attributes):
        super().__init__(operator)
        self.relation_name = relation_name
        self.attributes = attributes

    def __eq__(self, other):
        return (
            super().__eq__(other)
            and self.relation_name == other.relation_name
            and self.attributes == other.attributes
        )

    def post_order(self):
        return [self]


class UnaryDependencyNode(DependencyNode):
    pass


class BinaryDependencyNode(DependencyNode):
    left_child: RelationNode | SelectNode
    right_child: RelationNode | SelectNode


class PrimaryKeyNode(UnaryDependencyNode):
    """
    A node representing a primary key dependency.
    """

    def __init__(self, relation_name, attributes):
        super().__init__(Operator.primary_key, relation_name, attributes)


class MultivaluedDependencyNode(UnaryDependencyNode):
    """
    A node representing a multivalued dependency.
    """

    child: RelationNode | SelectNode

    def __init__(self, relation_name, attributes, relation_node):
        super().__init__(Operator.multivalued_dependency, relation_name, attributes)
        self.child = relation_node

    def __eq__(self, other):
        return super().__eq__(other) and self.child == other.child


class FunctionalDependencyNode(UnaryDependencyNode):
    """
    A node representing a functional dependency.
    """

    child: RelationNode | SelectNode

    def __init__(self, relation_name, attributes, relation_node):
        super().__init__(Operator.functional_dependency, relation_name, attributes)
        self.child = relation_node

    def __eq__(self, other):
        return super().__eq__(other) and self.child == other.child


class InclusionEquivalenceNode(BinaryDependencyNode):
    """
    A node representing an inclusion equivalence dependency.
    """

    left_child: RelationNode | SelectNode
    right_child: RelationNode | SelectNode

    def __init__(self, relation_names, attributes, left_child, right_child):
        super().__init__(Operator.inclusion_equivalence, relation_names, attributes)
        self.relation_names = relation_names
        self.left_child = left_child
        self.right_child = right_child

    def __eq__(self, other):
        return (
            super().__eq__(other)
            and self.relation_names == other.relation_names
            and self.left_child == other.left_child
            and self.right_child == other.right_child
        )


class InclusionSubsumptionNode(BinaryDependencyNode):
    """
    A node representing an inclusion subsumption dependency.
    """

    left_child: RelationNode | SelectNode
    right_child: RelationNode | SelectNode

    def __init__(self, relation_names, attributes, left_child, right_child):
        super().__init__(Operator.inclusion_subsumption, relation_names, attributes)
        self.relation_names = relation_names
        self.left_child = left_child
        self.right_child = right_child

    def __eq__(self, other):
        return (
            super().__eq__(other)
            and self.relation_names == other.relation_names
            and self.left_child == other.left_child
            and self.right_child == other.right_child
        )


class Operator(Enum):
    """
    A type of relational algebra operation.
    """

    # Basic operations
    relation = auto()
    assign = auto()
    definition = auto()
    project = auto()
    rename = auto()
    select = auto()

    # Join operations.
    cross_join = auto()
    natural_join = auto()
    theta_join = auto()
    full_outer_join = auto()
    left_outer_join = auto()
    right_outer_join = auto()

    # Set operations.
    difference = auto()
    union = auto()
    intersect = auto()

    # Dependency operations.
    primary_key = auto()
    multivalued_dependency = auto()
    functional_dependency = auto()
    inclusion_equivalence = auto()
    inclusion_subsumption = auto()
