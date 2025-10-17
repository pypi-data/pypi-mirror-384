import pytest

from src.rapt2.treebrd.grammars.dependency_grammar import DependencyGrammar
from src.rapt2.treebrd.node import (FunctionalDependencyNode,
                                    InclusionEquivalenceNode,
                                    InclusionSubsumptionNode,
                                    MultivaluedDependencyNode, Operator,
                                    PrimaryKeyNode, RelationNode, SelectNode)
from src.rapt2.treebrd.treebrd import TreeBRD


class TestDependencyGrammar:
    """Test cases for the DependencyGrammar class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.grammar = DependencyGrammar()
        self.schema = {"R": ["a", "b", "c"], "S": ["x", "y"], "T": ["id", "name"]}

    def test_primary_key_dependency_parsing(self):
        """Test parsing of primary key dependencies."""
        # Test single attribute primary key
        result = self.grammar.parse("pk_{a} R;")
        assert len(result) == 1
        assert result[0][0] == "pk"
        assert list(result[0][1]) == ["a"]
        assert result[0][2] == "r"

        # Test multiple attributes primary key
        result = self.grammar.parse("pk_{a, b} R;")
        assert len(result) == 1
        assert result[0][0] == "pk"
        assert list(result[0][1]) == ["a", "b"]
        assert result[0][2] == "r"

    def test_multivalued_dependency_parsing(self):
        """Test parsing of multivalued dependencies."""
        # Test simple multivalued dependency (without conditions)
        result = self.grammar.parse("mvd_{a, b} R;")
        assert len(result) == 1
        assert result[0][0] == "mvd"
        assert list(result[0][1]) == ["a", "b"]
        assert result[0][2] == "r"

        # Test multivalued dependency with conditions
        result = self.grammar.parse("mvd_{a, b} \\select_{a = 1} R;")
        assert len(result) == 1
        assert result[0][0] == "mvd"
        assert list(result[0][1]) == ["a", "b"]
        assert result[0][2] == "\\select"
        assert list(result[0][3][0]) == ["a", "=", "1"]
        assert result[0][4] == "r"

        # Test complex multivalued dependency with conditions
        result = self.grammar.parse("mvd_{a, b} \\select_{a = 1 and b > 0} R;")
        assert len(result) == 1
        assert result[0][0] == "mvd"
        assert list(result[0][1]) == ["a", "b"]
        assert result[0][2] == "\\select"
        assert result[0][4] == "r"

    def test_functional_dependency_parsing(self):
        """Test parsing of functional dependencies."""
        # Test simple functional dependency (without conditions)
        result = self.grammar.parse("fd_{a, b} R;")
        assert len(result) == 1
        assert result[0][0] == "fd"
        assert list(result[0][1]) == ["a", "b"]
        assert result[0][2] == "r"

        # Test functional dependency with conditions
        result = self.grammar.parse("fd_{a, b} \\select_{a = 1} R;")
        assert len(result) == 1
        assert result[0][0] == "fd"
        assert list(result[0][1]) == ["a", "b"]
        assert result[0][2] == "\\select"
        assert list(result[0][3][0]) == ["a", "=", "1"]
        assert result[0][4] == "r"

        # Test complex functional dependency with conditions
        result = self.grammar.parse("fd_{a, b} \\select_{a = 1 and b > 0} R;")
        assert len(result) == 1
        assert result[0][0] == "fd"
        assert list(result[0][1]) == ["a", "b"]
        assert result[0][2] == "\\select"
        assert result[0][4] == "r"

    def test_simple_functional_dependency_parsing(self):
        """Test parsing of simple functional dependencies without conditions."""
        # Test simple functional dependency without conditions
        result = self.grammar.parse("fd_{a, b} R;")
        assert len(result) == 1
        assert result[0][0] == "fd"
        assert list(result[0][1]) == ["a", "b"]
        assert result[0][2] == "r"

    def test_inclusion_equivalence_parsing(self):
        """Test parsing of inclusion equivalence dependencies."""
        # Test simple inclusion equivalence
        result = self.grammar.parse("inc=_{a, b} (R, S);")
        assert len(result) == 1
        assert result[0][0] == "inc="
        assert list(result[0][1]) == ["a", "b"]
        assert len(result[0][2]) == 2
        assert result[0][2][0][0] == "r"
        assert result[0][2][1][0] == "s"

        # Test inclusion equivalence with select on left
        result = self.grammar.parse("inc=_{a, b} (\\select_{a = 1} R, S);")
        assert len(result) == 1
        assert result[0][0] == "inc="
        assert list(result[0][1]) == ["a", "b"]
        assert len(result[0][2]) == 2
        assert result[0][2][0][0] == "\\select"
        assert result[0][2][1][0] == "s"

        # Test inclusion equivalence with select on both sides
        result = self.grammar.parse("inc=_{a, b} (\\select_{a = 1} R, \\select_{x > 0} S);")
        assert len(result) == 1
        assert result[0][0] == "inc="
        assert list(result[0][1]) == ["a", "b"]
        assert len(result[0][2]) == 2
        assert result[0][2][0][0] == "\\select"
        assert result[0][2][1][0] == "\\select"

    def test_inclusion_subsumption_parsing(self):
        """Test parsing of inclusion subsumption dependencies."""
        # Test simple inclusion subsumption
        result = self.grammar.parse("inc⊆_{a, b} (R, S);")
        assert len(result) == 1
        assert result[0][0] == "inc⊆"
        assert list(result[0][1]) == ["a", "b"]
        assert len(result[0][2]) == 2
        assert result[0][2][0][0] == "r"
        assert result[0][2][1][0] == "s"

        # Test inclusion subsumption with select on left
        result = self.grammar.parse("inc⊆_{a, b} (\\select_{a = 1} R, S);")
        assert len(result) == 1
        assert result[0][0] == "inc⊆"
        assert list(result[0][1]) == ["a", "b"]
        assert len(result[0][2]) == 2
        assert result[0][2][0][0] == "\\select"
        assert result[0][2][1][0] == "s"

    def test_multiple_statements_parsing(self):
        """Test parsing of multiple dependency statements."""
        result = self.grammar.parse(
            "pk_{a} R; mvd_{b, c} \\select_{b > 0} S; fd_{x, y} \\select_{x > 0} T;"
        )
        assert len(result) == 3

        # Check first statement (primary key)
        assert result[0][0] == "pk"
        assert list(result[0][1]) == ["a"]
        assert result[0][2] == "r"

        # Check second statement (multivalued dependency with select)
        assert result[1][0] == "mvd"
        assert list(result[1][1]) == ["b", "c"]
        assert result[1][2] == "\\select"
        assert result[1][4] == "s"

        # Check third statement (functional dependency)
        assert result[2][0] == "fd"
        assert list(result[2][1]) == ["x", "y"]
        assert result[2][2] == "\\select"
        assert result[2][4] == "t"

    def test_invalid_syntax_raises_error(self):
        """Test that invalid syntax raises parsing errors."""
        with pytest.raises(Exception):
            self.grammar.parse("invalid syntax")

        with pytest.raises(Exception):
            self.grammar.parse("pk_{a} R")  # Missing semicolon

        with pytest.raises(Exception):
            self.grammar.parse("unknown_{a} R;")  # Unknown operator


class TestDependencyGrammarIntegration:
    """Test integration of DependencyGrammar with TreeBRD."""

    def setup_method(self):
        """Set up test fixtures."""
        self.grammar = DependencyGrammar()
        self.schema = {"R": ["a", "b", "c"], "S": ["x", "y"], "T": ["id", "name"]}
        self.builder = TreeBRD(self.grammar)

    def test_primary_key_node_creation(self):
        """Test creation of PrimaryKeyNode from dependency statements."""
        trees = self.builder.build("pk_{a, b} R;", self.schema)
        assert len(trees) == 1

        node = trees[0]
        assert isinstance(node, PrimaryKeyNode)
        assert node.operator == Operator.primary_key
        assert node.relation_name == "r"
        assert list(node.attributes) == ["a", "b"]

    def test_multivalued_dependency_node_creation(self):
        """Test creation of MultivaluedDependencyNode from dependency statements."""
        # Test simple multivalued dependency (without conditions)
        trees = self.builder.build("mvd_{a, b} R;", self.schema)
        assert len(trees) == 1

        node = trees[0]
        assert isinstance(node, MultivaluedDependencyNode)
        assert node.operator == Operator.multivalued_dependency
        assert node.relation_name == "r"
        assert list(node.attributes) == ["a", "b"]
        assert node.child is not None
        assert isinstance(node.child, RelationNode)

    def test_multivalued_dependency_node_creation_with_conditions(self):
        """Test creation of MultivaluedDependencyNode from dependency statements with conditions."""
        trees = self.builder.build("mvd_{a, b} \\select_{a = 1} R;", self.schema)
        assert len(trees) == 1

        node = trees[0]
        assert isinstance(node, MultivaluedDependencyNode)
        assert node.operator == Operator.multivalued_dependency
        assert node.relation_name == "r"
        assert list(node.attributes) == ["a", "b"]
        assert node.child is not None
        assert isinstance(node.child, SelectNode)

    def test_functional_dependency_node_creation_with_conditions(self):
        """Test creation of FunctionalDependencyNode from dependency statements with conditions."""
        trees = self.builder.build("fd_{a, b} \\select_{a = 1} R;", self.schema)
        assert len(trees) == 1

        node = trees[0]
        assert isinstance(node, FunctionalDependencyNode)
        assert node.operator == Operator.functional_dependency
        assert node.relation_name == "r"
        assert list(node.attributes) == ["a", "b"]
        assert node.child is not None
        assert isinstance(node.child, SelectNode)

    def test_functional_dependency_node_creation_simple(self):
        """Test creation of FunctionalDependencyNode from simple dependency statements."""
        trees = self.builder.build("fd_{a, b} R;", self.schema)
        assert len(trees) == 1

        node = trees[0]
        assert isinstance(node, FunctionalDependencyNode)
        assert node.operator == Operator.functional_dependency
        assert node.relation_name == "r"
        assert list(node.attributes) == ["a", "b"]
        assert node.child is not None
        assert isinstance(node.child, RelationNode)

    def test_inclusion_equivalence_node_creation(self):
        """Test creation of InclusionEquivalenceNode from dependency statements."""
        # Test simple inclusion equivalence
        trees = self.builder.build("inc=_{a, b} (R, S);", self.schema)
        assert len(trees) == 1

        node = trees[0]
        assert isinstance(node, InclusionEquivalenceNode)
        assert node.operator == Operator.inclusion_equivalence
        assert list(node.relation_names) == ["r", "s"]
        assert list(node.attributes) == ["a", "b"]
        assert isinstance(node.left_child, RelationNode)
        assert isinstance(node.right_child, RelationNode)

    def test_inclusion_equivalence_node_creation_with_select(self):
        """Test creation of InclusionEquivalenceNode with select clauses."""
        trees = self.builder.build("inc=_{a, b} (\\select_{a = 1} R, S);", self.schema)
        assert len(trees) == 1

        node = trees[0]
        assert isinstance(node, InclusionEquivalenceNode)
        assert node.operator == Operator.inclusion_equivalence
        assert list(node.relation_names) == ["r", "s"]
        assert list(node.attributes) == ["a", "b"]
        assert isinstance(node.left_child, SelectNode)
        assert isinstance(node.right_child, RelationNode)

    def test_inclusion_subsumption_node_creation(self):
        """Test creation of InclusionSubsumptionNode from dependency statements."""
        # Test simple inclusion subsumption
        trees = self.builder.build("inc⊆_{a, b} (R, S);", self.schema)
        assert len(trees) == 1

        node = trees[0]
        assert isinstance(node, InclusionSubsumptionNode)
        assert node.operator == Operator.inclusion_subsumption
        assert list(node.relation_names) == ["r", "s"]
        assert list(node.attributes) == ["a", "b"]
        assert isinstance(node.left_child, RelationNode)
        assert isinstance(node.right_child, RelationNode)

    def test_inclusion_subsumption_node_creation_with_select(self):
        """Test creation of InclusionSubsumptionNode with select clauses."""
        trees = self.builder.build("inc⊆_{a, b} (\\select_{a = 1} R, S);", self.schema)
        assert len(trees) == 1

        node = trees[0]
        assert isinstance(node, InclusionSubsumptionNode)
        assert node.operator == Operator.inclusion_subsumption
        assert list(node.relation_names) == ["r", "s"]
        assert list(node.attributes) == ["a", "b"]
        assert isinstance(node.left_child, SelectNode)
        assert isinstance(node.right_child, RelationNode)

    def test_multiple_dependency_statements(self):
        """Test parsing multiple dependency statements into multiple nodes."""
        trees = self.builder.build(
            "pk_{a} R; mvd_{x, y} \\select_{x > 0} S; fd_{id, name} \\select_{id > 0} T;", self.schema
        )
        assert len(trees) == 3

        # Check first node (primary key)
        assert isinstance(trees[0], PrimaryKeyNode)
        assert trees[0].relation_name == "r"

        # Check second node (multivalued dependency with select)
        assert isinstance(trees[1], MultivaluedDependencyNode)
        assert trees[1].relation_name == "s"
        assert isinstance(trees[1].child, SelectNode)

        # Check third node (functional dependency)
        assert isinstance(trees[2], FunctionalDependencyNode)
        assert trees[2].relation_name == "t"

    def test_dependency_node_equality(self):
        """Test equality comparison of dependency nodes."""
        trees1 = self.builder.build("pk_{a, b} R;", self.schema)
        trees2 = self.builder.build("pk_{a, b} R;", self.schema)

        # Test that nodes have the same properties
        node1 = trees1[0]
        node2 = trees2[0]
        assert node1.operator == node2.operator
        assert node1.relation_name == node2.relation_name
        assert list(node1.attributes) == list(node2.attributes)

        # Test inequality
        trees3 = self.builder.build("pk_{a, c} R;", self.schema)
        node3 = trees3[0]
        assert list(node1.attributes) != list(node3.attributes)

    def test_dependency_node_post_order(self):
        """Test post-order traversal of dependency nodes."""
        trees = self.builder.build("pk_{a, b} R;", self.schema)
        node = trees[0]

        post_order = node.post_order()
        assert len(post_order) == 1
        assert post_order[0] == node


class TestDependencyGrammarWithRapt:
    """Test DependencyGrammar integration with the main Rapt class."""

    def setup_method(self):
        """Set up test fixtures."""
        from src.rapt2.rapt import Rapt

        self.rapt = Rapt(grammar="Dependency Grammar")
        self.schema = {"R": ["a", "b", "c"], "S": ["x", "y"], "T": ["id", "name"]}

    def test_dependency_grammar_selection(self):
        """Test that DependencyGrammar can be selected via Rapt configuration."""
        assert self.rapt.builder.grammar.__class__.__name__ == "DependencyGrammar"

    def test_dependency_syntax_tree_generation(self):
        """Test generation of syntax trees for dependency statements."""
        trees = self.rapt.to_syntax_tree("pk_{a, b} R;", self.schema)
        assert len(trees) == 1
        assert isinstance(trees[0], PrimaryKeyNode)

    def test_multiple_dependency_syntax_trees(self):
        """Test generation of multiple syntax trees for multiple dependency statements."""
        trees = self.rapt.to_syntax_tree(
            "pk_{a} R; mvd_{x, y} \\select_{x > 0} S; fd_{id, name} \\select_{id > 0} T;", self.schema
        )
        assert len(trees) == 3
        assert isinstance(trees[0], PrimaryKeyNode)
        assert isinstance(trees[1], MultivaluedDependencyNode)
        assert isinstance(trees[1].child, SelectNode)
        assert isinstance(trees[2], FunctionalDependencyNode)
