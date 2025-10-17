from typing import Union
from ...treebrd.node import (Operator, AssignNode, CrossJoinNode, 
                            DifferenceNode, FullOuterJoinNode,
                            IntersectNode, LeftOuterJoinNode,
                            NaturalJoinNode, PrimaryKeyNode, ProjectNode, RelationNode,
                            RenameNode, RightOuterJoinNode, SelectNode, ThetaJoinNode,
                            UnionNode)
from ...treebrd.condition_node import (BinaryConditionNode, ConditionNode,
                                       IdentityConditionNode, UnaryConditionNode,
                                       BinaryConditionalOperator, UnaryConditionalOperator)
from ..base_translator import BaseTranslator


class SQLQuery:
    """
    Structure defining the building blocks of a SQL query.
    """

    def __init__(self, select_block, from_block, where_block=""):
        self.prefix = ""
        self.select_block = select_block
        self.from_block = from_block
        self.where_block = where_block

    @property
    def _basic_query(self):
        if self.select_block:
            return "{prefix}SELECT {select} FROM {relation}"
        else:
            return "{prefix}{relation}"

    @property
    def _sql_query_skeleton(self):
        sql = self._basic_query
        if self.where_block:
            sql += " WHERE {conditions}"
        return sql

    def to_sql(self):
        """
        Construct a SQL query based on the stored blocks.
        :return: a SQL query
        """
        return self._sql_query_skeleton.format(
            prefix=self.prefix,
            select=self.select_block,
            relation=self.from_block,
            conditions=self.where_block,
        )


class SQLSetQuery(SQLQuery):
    """
    Structure defining the building blocks of a SQL query with set semantics.
    """

    @property
    def _basic_query(self):
        return "{prefix}SELECT DISTINCT {select} FROM {relation}"


class SQLAlterTableQuery(SQLQuery):
    """
    Structure defining an ALTER TABLE SQL statement.
    """

    def __init__(self, table_name, action, attributes):
        """
        Initialize an ALTER TABLE query with table name, action, and attributes.
        :param table_name: The name of the table to alter
        :param action: The alteration action (e.g., "ADD PRIMARY KEY")
        :param attributes: The attributes involved in the action (as a string)
        """
        super().__init__(select_block="", from_block="")
        self.table_name = table_name
        self.action = action
        self.attributes = attributes

    def to_sql(self):
        """
        Return the ALTER TABLE statement directly.
        :return: The ALTER TABLE statement
        """
        return f"ALTER TABLE {self.table_name} {self.action} ({self.attributes})"


class SQLTranslator(BaseTranslator):
    """
    A Translator defining the operations for translating a relational algebra
    statement into a SQL statement using bag semantics.
    """

    query = SQLQuery

    @classmethod
    def _get_temp_name(cls, node):
        return node.name or "_{}".format(id(node))

    def _get_sql_operator(self, node: Union[NaturalJoinNode, ThetaJoinNode, CrossJoinNode, 
                                           FullOuterJoinNode, LeftOuterJoinNode, RightOuterJoinNode,
                                           UnionNode, DifferenceNode, IntersectNode]) -> str:
        operators = {
            Operator.union: "UNION",
            Operator.difference: "EXCEPT",
            Operator.intersect: "INTERSECT",
            Operator.cross_join: "CROSS JOIN",
            Operator.theta_join: "JOIN",
            Operator.natural_join: "NATURAL JOIN",
            Operator.full_outer_join: "FULL OUTER JOIN",
            Operator.left_outer_join: "LEFT OUTER JOIN",
            Operator.right_outer_join: "RIGHT OUTER JOIN",
        }
        return operators[node.operator]

    def relation(self, node: RelationNode) -> SQLQuery:
        """
        Translate a relation node into SQLQuery.
        :param node: a treebrd node
        :return: a SQLQuery object for the tree rooted at node
        """
        return self.query(select_block=str(node.attributes), from_block=node.name)

    def select(self, node: SelectNode) -> SQLQuery:
        """
        Translate a select node into SQLQuery.
        :param node: a treebrd node
        :return: a SQLQuery object for the tree rooted at node
        """

        child_object = self.translate(node.child)
        where_block = self.translate_condition(node.conditions)
        if child_object.where_block:
            where_block = "({0}) AND ({1})".format(
                child_object.where_block, self.translate_condition(node.conditions)
            )
        child_object.where_block = where_block
        if not child_object.select_block:
            child_object.select_block = str(node.attributes)
        return child_object

    def project(self, node: ProjectNode) -> SQLQuery:
        """
        Translate a project node into SQLQuery.
        :param node: a treebrd node
        :return: a SQLQuery object for the tree rooted at node
        """
        child_object = self.translate(node.child)
        child_object.select_block = str(node.attributes)
        return child_object

    def rename(self, node: RenameNode) -> SQLQuery:
        """
        Translate a rename node into SQLQuery.
        :param node: a treebrd node
        :return: a SQLQuery object for the tree rooted at node
        """
        child_object = self.translate(node.child)
        from_block = "({child}) AS {name}({attributes})".format(
            child=child_object.to_sql(),
            name=node.name,
            attributes=", ".join(node.attributes.names),
        )
        return self.query(str(node.attributes), from_block=from_block)

    def assign(self, node: AssignNode) -> SQLQuery:
        """
        Translate an assign node into SQLQuery.
        :param node: a treebrd node
        :return: a SQLQuery object for the tree rooted at node
        """
        child_object = self.translate(node.child)
        child_object.prefix = "CREATE TEMPORARY TABLE {name}({attributes}) AS ".format(
            name=node.name, attributes=", ".join(node.attributes.names)
        )
        return child_object

    def definition(self, node) -> None:
        """
        Ignore definition nodes during SQL translation.
        :param node: a DefinitionNode
        :return: None
        """
        return None

    def natural_join(self, node: NaturalJoinNode) -> SQLQuery:
        """
        Translate an assign node into SQLQuery.
        :param node: a treebrd node
        :return: a SQLQuery object for the tree rooted at node
        """
        return self._join(node)

    def theta_join(self, node: ThetaJoinNode) -> SQLQuery:
        """
        Translate an assign node into SQLQuery.
        :param node: a treebrd node
        :return: a SQLQuery object for the tree rooted at node
        """
        return self._join(node)

    def cross_join(self, node: CrossJoinNode) -> SQLQuery:
        """
        Translate a cross join node into SQLQuery.
        :param node: a treebrd node
        :return: a SQLQuery object for the tree rooted at node
        """
        return self._join(node)

    def full_outer_join(self, node: FullOuterJoinNode) -> SQLQuery:
        """
        Translate a full outer join node into SQLQuery.
        :param node: a treebrd node
        :return: a SQLQuery object for the tree rooted at node
        """
        return self._join(node)

    def left_outer_join(self, node: LeftOuterJoinNode) -> SQLQuery:
        """
        Translate a left outer join node into SQLQuery.
        :param node: a treebrd node
        :return: a SQLQuery object for the tree rooted at node
        """
        return self._join(node)

    def right_outer_join(self, node: RightOuterJoinNode) -> SQLQuery:
        """
        Translate a right outer join node into SQLQuery.
        :param node: a treebrd node
        :return: a SQLQuery object for the tree rooted at node
        """
        return self._join(node)

    def union(self, node: UnionNode) -> SQLQuery:
        """
        Translate a union node into SQLQuery.
        :param node: a treebrd node
        :return: a SQLQuery object for the tree rooted at node
        """
        return self._set_op(node)

    def intersect(self, node: IntersectNode) -> SQLQuery:
        """
        Translate an intersection node into SQLQuery.
        :param node: a treebrd node
        :return: a SQLQuery object for the tree rooted at node
        """
        return self._set_op(node)

    def difference(self, node: DifferenceNode) -> SQLQuery:
        """
        Translate an difference node into SQLQuery.
        :param node: a treebrd node
        :return: a SQLQuery object for the tree rooted at node
        """
        return self._set_op(node)

    def _join_helper(self, node: Union[RelationNode, SelectNode, ProjectNode, RenameNode, 
                                      NaturalJoinNode, ThetaJoinNode, CrossJoinNode,
                                      FullOuterJoinNode, LeftOuterJoinNode, RightOuterJoinNode,
                                      UnionNode, DifferenceNode, IntersectNode]) -> str:
        sobject = self.translate(node)
        if node.operator in {
            Operator.cross_join,
            Operator.natural_join,
            Operator.theta_join,
            Operator.full_outer_join,
            Operator.left_outer_join,
            Operator.right_outer_join,
        }:
            return sobject.from_block
        else:
            return "({subquery}) AS {name}".format(
                subquery=sobject.to_sql(), name=self._get_temp_name(node)
            )

    def _join(self, node: Union[NaturalJoinNode, ThetaJoinNode, CrossJoinNode,
                               FullOuterJoinNode, LeftOuterJoinNode, RightOuterJoinNode]) -> SQLQuery:
        """
        Translate a join node into SQLQuery.
        :param node: a treebrd node
        :return: a SQLQuery object for the tree rooted at node
        """

        select_block = str(node.attributes)
        from_block = "{left} {operator} {right}".format(
            left=self._join_helper(node.left),
            right=self._join_helper(node.right),
            operator=self._get_sql_operator(node),
        )

        if node.operator in {
            Operator.theta_join,
            Operator.full_outer_join,
            Operator.left_outer_join,
            Operator.right_outer_join,
        }:
            # Only theta joins and outer joins have conditions
            if hasattr(node, 'conditions') and getattr(node, 'conditions', None) is not None:
                conditions = getattr(node, 'conditions')
                from_block = "{from_block} ON {conditions}".format(
                    from_block=from_block, conditions=self.translate_condition(conditions)
                )

        return self.query(select_block, from_block, "")

    def _set_op(self, node: Union[UnionNode, DifferenceNode, IntersectNode]) -> SQLQuery:
        """
        Translate a set operator node into SQLQuery.
        :param node: a treebrd node
        :return: a SQLQuery object for the tree rooted at node
        """
        select_block = str(node.attributes)
        from_block = "({left} {operator} ALL {right}) AS {name}".format(
            left=self.translate(node.left).to_sql(),
            right=self.translate(node.right).to_sql(),
            operator=self._get_sql_operator(node),
            name=self._get_temp_name(node),
        )
        return self.query(select_block=select_block, from_block=from_block)

    def identity_condition(self, node: IdentityConditionNode) -> str:
        """
        Translate an identity condition node into SQL.
        :param node: an identity condition node
        :return: SQL representation of the condition
        """
        return node.ident

    def unary_condition(self, node: UnaryConditionNode) -> str:
        """
        Translate a unary condition node into SQL.
        :param node: a unary condition node
        :return: SQL representation of the condition
        """
        match node.op:
            case UnaryConditionalOperator.NOT:
                return f"NOT {self.translate_condition(node.child)}"
            case UnaryConditionalOperator.DEFINED:
                return f"{self.translate_condition(node.child)} IS NOT NULL"
            case _:
                raise ValueError

    def binary_condition(self, node: BinaryConditionNode) -> str:
        """
        Translate a binary condition node into SQL.
        :param node: a binary condition node
        :return: SQL representation of the condition
        """
        match node.op:
            case BinaryConditionalOperator.AND:
                return f"({self.translate_condition(node.left)} AND {self.translate_condition(node.right)})"
            case BinaryConditionalOperator.OR:
                return f"({self.translate_condition(node.left)} OR {self.translate_condition(node.right)})"
            case BinaryConditionalOperator.EQUAL:
                return f"({self.translate_condition(node.left)} = {self.translate_condition(node.right)})"
            case BinaryConditionalOperator.NOT_EQUAL:
                return f"({self.translate_condition(node.left)} != {self.translate_condition(node.right)})"
            case BinaryConditionalOperator.LESS_THAN:
                return f"({self.translate_condition(node.left)} < {self.translate_condition(node.right)})"
            case BinaryConditionalOperator.LESS_THAN_EQUAL:
                return f"({self.translate_condition(node.left)} <= {self.translate_condition(node.right)})"
            case BinaryConditionalOperator.GREATER_THAN:
                return f"({self.translate_condition(node.left)} > {self.translate_condition(node.right)})"
            case BinaryConditionalOperator.GREATER_THAN_EQUAL:
                return f"({self.translate_condition(node.left)} >= {self.translate_condition(node.right)})"
            case _:
                raise ValueError

    def primary_key(self, node: PrimaryKeyNode) -> SQLAlterTableQuery:
        """
        Translate a primary key dependency node into SQL.
        :param node: a PrimaryKeyNode
        :return: a SQLAlterTableQuery object representing the primary key constraint
        """
        # Convert attributes to comma-separated string
        if hasattr(node.attributes, '__iter__') and not isinstance(node.attributes, str):
            attributes_str = ", ".join(str(attr) for attr in node.attributes)
        else:
            attributes_str = str(node.attributes)
        
        return SQLAlterTableQuery(
            table_name=node.relation_name,
            action="ADD PRIMARY KEY",
            attributes=attributes_str
        )

    def multivalued_dependency(self, node) -> None:
        """
        Ignore multivalued dependency nodes during SQL translation.
        :param node: a MultivaluedDependencyNode
        :return: None
        """
        # TODO: Implement multivalued dependency translation
        return None

    def functional_dependency(self, node) -> None:
        """
        Ignore functional dependency nodes during SQL translation.
        :param node: a FunctionalDependencyNode
        :return: None
        """
        # TODO: Implement functional dependency translation
        return None

    def inclusion_equivalence(self, node) -> None:
        """
        Ignore inclusion equivalence nodes during SQL translation.
        :param node: an InclusionEquivalenceNode
        :return: None
        """
        # TODO: Implement inclusion equivalence translation
        return None

    def inclusion_subsumption(self, node) -> None:
        """
        Ignore inclusion subsumption nodes during SQL translation.
        :param node: an InclusionSubsumptionNode
        :return: None
        """
        # TODO: Implement inclusion subsumption translation
        return None

    def translate_condition(self, condition: Union[ConditionNode, BinaryConditionNode, 
                                                 UnaryConditionNode, IdentityConditionNode]) -> str:
        """
        Translate a condition node into SQL.
        :param condition: a condition node
        :return: SQL representation of the condition
        """
        if isinstance(condition, IdentityConditionNode):
            return self.identity_condition(condition)
        elif isinstance(condition, UnaryConditionNode):
            return self.unary_condition(condition)
        elif isinstance(condition, BinaryConditionNode):
            return self.binary_condition(condition)
        else:
            raise ValueError(f"Unknown condition node type: {type(condition)}")


class SetTranslator(SQLTranslator):
    """
    A Translator defining the operations for translating a relational algebra
    statement into a SQL statement using set semantics.
    """

    query = SQLSetQuery

    def _set_op(self, node: Union[UnionNode, DifferenceNode, IntersectNode]) -> SQLSetQuery:
        """
        Translate a set operator node into SQLQuery, using set semantics.
        :param node: a treebrd node
        :return: a SQLSetQuery object for the tree rooted at node
        """
        select_block = str(node.attributes)
        from_block = "({left} {operator} {right}) AS {name}".format(
            left=self.translate(node.left).to_sql(),
            right=self.translate(node.right).to_sql(),
            operator=self._get_sql_operator(node),
            name=self._get_temp_name(node),
        )
        return self.query(select_block=select_block, from_block=from_block)


def translate(root_list, use_bag_semantics=False, syntax=None):
    """
    Translate a list of relational algebra trees into SQL statements.

    :param root_list: a list of tree roots
    :param use_bag_semantics: flag for using relational algebra bag semantics
    :param syntax: syntax instance for custom operators
    :return: a list of SQL statements
    """
    translator = SQLTranslator(syntax) if use_bag_semantics else SetTranslator(syntax)  # type: ignore
    results = []
    for root in root_list:
        translated = translator.translate(root)
        if translated is not None:
            results.append(translated.to_sql())
    return results
