import pytest

from rapt2.rapt import Rapt
from rapt2.transformers.qtree.constants import *
from rapt2.treebrd.grammars.dependency_grammar import DependencyGrammar
from rapt2.treebrd.grammars.extended_grammar import ExtendedGrammar
from rapt2.treebrd.treebrd import TreeBRD
from tests.transformers.test_transfomer import TestTransformer


class TestQTreeTransformer(TestTransformer):
    def setUp(self):
        self.translate = self.translate_func(Rapt(grammar="Extended Grammar").to_qtree)


class TestQTreeDependencyTransformer(TestTransformer):
    def setUp(self):
        self.rapt = Rapt(grammar="Dependency Grammar")
        self.translate = self.translate_func(self.rapt.to_qtree)


class TestRelation(TestQTreeTransformer):
    def test_single_relation(self):
        ra = "alpha;"
        expected = [r"\Tree[.$alpha$ ]"]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_multiple_relations(self):
        ra = "alpha; beta;"
        expected = [r"\Tree[.$alpha$ ]", r"\Tree[.$beta$ ]"]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestSelect(TestQTreeTransformer):
    def test_simple(self):
        ra = r"\select_{a1=a2} alpha;"
        expected = [r"\Tree[.${}_{{(a1 \eq a2)}}$ [.$alpha$ ] ]".format(SELECT_OP)]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestProject(TestQTreeTransformer):
    def test_simple(self):
        ra = r"\project_{a1, a2, a3} alpha;"
        expected = [r"\Tree[.${}_{{a1,\,a2,\,a3}}$ [.$alpha$ ] ]".format(PROJECT_OP)]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestRename(TestQTreeTransformer):
    def test_rename_relation(self):
        ra = r"\rename_{Apex} alpha;"
        expected = [r"\Tree[.${}_{{apex(a1,\,a2,\,a3)}}$ [.$alpha$ ] ]".format(RENAME_OP)]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_rename_attributes(self):
        ra = r"\rename_{(a, b, c)} alpha;"
        expected = [r"\Tree[.${}_{{alpha(a,\,b,\,c)}}$ [.$alpha$ ] ]".format(RENAME_OP)]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_rename_relation_and_attributes(self):
        ra = r"\rename_{apex(a, b, c)} alpha;"
        expected = [r"\Tree[.${}_{{apex(a,\,b,\,c)}}$ [.$alpha$ ] ]".format(RENAME_OP)]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestAssignment(TestQTreeTransformer):
    def test_relation(self):
        ra = "new_alpha := alpha;"
        expected = [r"\Tree[.$new\_alpha(a1,\,a2,\,a3)$ [.$alpha$ ] ]"]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_relation_with_attributes(self):
        ra = "new_alpha(a, b, c) := alpha;"
        expected = [r"\Tree[.$new\_alpha(a,\,b,\,c)$ [.$alpha$ ] ]"]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestDefinition(TestQTreeTransformer):
    def test_single_attribute(self):
        ra = "R(a);"
        expected = [r"\Tree[.$r(a)$ ]"]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_multiple_attributes(self):
        ra = "R(a, b, c);"
        expected = [r"\Tree[.$r(a,\,b,\,c)$ ]"]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_two_attributes(self):
        ra = "R(a, b);"
        expected = [r"\Tree[.$r(a,\,b)$ ]"]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_multiple_definitions(self):
        ra = "R1(a, b); R2(c, d);"
        expected = [
            r"\Tree[.$r1(a,\,b)$ ]",
            r"\Tree[.$r2(c,\,d)$ ]"
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_definition_with_spacing(self):
        ra = "R ( a , b , c ) ;"
        expected = [r"\Tree[.$r(a,\,b,\,c)$ ]"]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestJoin(TestQTreeTransformer):
    def test_relation(self):
        ra = r"alpha \join beta;"
        expected = [r"\Tree[.${}$ [.$alpha$ ] [.$beta$ ] ]".format(JOIN_OP)]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestNaturalJoin(TestQTreeTransformer):
    grammar = ExtendedGrammar

    def test_relation(self):
        ra = r"alpha \natural_join beta;"
        expected = [r"\Tree[.${}$ [.$alpha$ ] [.$beta$ ] ]".format(NATURAL_JOIN_OP)]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestThetaJoin(TestQTreeTransformer):
    grammar = ExtendedGrammar

    def test_relation(self):
        ra = r"alpha \join_{a1 = b1} beta;"
        expected = [
            r"\Tree[.${}_{{(a1 \eq b1)}}$ [.$alpha$ ] [.$beta$ ] ]".format(
                THETA_JOIN_OP
            )
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestFullOuterJoin(TestQTreeTransformer):
    grammar = ExtendedGrammar

    def test_relation(self):
        ra = r"alpha \full_outer_join_{a1 = b1} beta;"
        expected = [
            r"\Tree[.${}_{{(a1 \eq b1)}}$ [.$alpha$ ] [.$beta$ ] ]".format(
                FULL_OUTER_JOIN_OP
            )
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_complex_condition(self):
        ra = r"alpha \full_outer_join_{alpha.a1=beta.b1 and b3>50} beta;"
        expected = [
            r"\Tree[.${}_{{((alpha.a1 \eq beta.b1) \land (b3 \gt 50))}}$ [.$alpha$ ] [.$beta$ ] ]".format(
                FULL_OUTER_JOIN_OP
            )
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestLeftOuterJoin(TestQTreeTransformer):
    grammar = ExtendedGrammar

    def test_relation(self):
        ra = r"alpha \left_outer_join_{a1 = b1} beta;"
        expected = [
            r"\Tree[.${}_{{(a1 \eq b1)}}$ [.$alpha$ ] [.$beta$ ] ]".format(
                LEFT_OUTER_JOIN_OP
            )
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_complex_condition(self):
        ra = r"alpha \left_outer_join_{alpha.a1=beta.b1 and b3>50} beta;"
        expected = [
            r"\Tree[.${}_{{((alpha.a1 \eq beta.b1) \land (b3 \gt 50))}}$ [.$alpha$ ] [.$beta$ ] ]".format(
                LEFT_OUTER_JOIN_OP
            )
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestRightOuterJoin(TestQTreeTransformer):
    grammar = ExtendedGrammar

    def test_relation(self):
        ra = r"alpha \right_outer_join_{a1 = b1} beta;"
        expected = [
            r"\Tree[.${}_{{(a1 \eq b1)}}$ [.$alpha$ ] [.$beta$ ] ]".format(
                RIGHT_OUTER_JOIN_OP
            )
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_complex_condition(self):
        ra = r"alpha \right_outer_join_{alpha.a1=beta.b1 and b3>50} beta;"
        expected = [
            r"\Tree[.${}_{{((alpha.a1 \eq beta.b1) \land (b3 \gt 50))}}$ [.$alpha$ ] [.$beta$ ] ]".format(
                RIGHT_OUTER_JOIN_OP
            )
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestUnion(TestQTreeTransformer):
    def test_simple(self):
        ra = r"gamma \union gammatwin;"
        expected = [r"\Tree[.${}$ [.$gamma$ ] [.$gammatwin$ ] ]".format(UNION_OP)]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestIntersect(TestQTreeTransformer):
    grammar = ExtendedGrammar

    def test_simple(self):
        ra = r"gamma \intersect gammatwin;"
        expected = [r"\Tree[.${}$ [.$gamma$ ] [.$gammatwin$ ] ]".format(INTERSECT_OP)]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestDifference(TestQTreeTransformer):
    def test_simple(self):
        ra = r"gamma \difference gammatwin;"
        expected = [r"\Tree[.${}$ [.$gamma$ ] [.$gammatwin$ ] ]".format(DIFFERENCE_OP)]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestFunctionalDependency(TestQTreeDependencyTransformer):
    def setUp(self):
        """Set up test fixtures with proper schema."""
        super().setUp()
        # Override the schema to include the attributes we need for functional dependencies
        self.schema = {
            "alpha": ["a", "b", "c"],
            "beta": ["c", "d", "e"],
            "gamma": ["id", "name", "value"],
        }
        # Update the translate function to use our custom schema
        self.translate = self.translate_func(self.rapt.to_qtree, schema=self.schema)

    def test_simple_functional_dependency(self):
        """Test simple functional dependency without select condition."""
        ra = "fd_{a, b} alpha;"
        expected = [r"\Tree[.$alpha : a \rightarrow b$ ]"]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_functional_dependency_with_simple_select(self):
        """Test functional dependency with simple select condition."""
        ra = "fd_{a, b} \\select_{a = 1} alpha;"
        expected = [r"\Tree[.$\sigma_{(a \eq 1)} (alpha) : a \rightarrow b$ ]"]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_functional_dependency_with_complex_select(self):
        """Test functional dependency with complex select condition."""
        ra = "fd_{a, b} \\select_{a = 1 and b > 0} alpha;"
        expected = [
            r"\Tree[.$\sigma_{((a \eq 1) \land (b \gt 0))} (alpha) : a \rightarrow b$ ]"
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_functional_dependency_with_different_attributes(self):
        """Test functional dependency with different attribute names."""
        ra = "fd_{id, name} \\select_{id > 0} gamma;"
        expected = [r"\Tree[.$\sigma_{(id \gt 0)} (gamma) : id \rightarrow name$ ]"]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_functional_dependency_with_or_condition(self):
        """Test functional dependency with OR condition in select."""
        ra = "fd_{a, b} \\select_{a = 1 or a = 2} alpha;"
        expected = [
            r"\Tree[.$\sigma_{((a \eq 1) \lor (a \eq 2))} (alpha) : a \rightarrow b$ ]"
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_functional_dependency_with_not_condition(self):
        """Test functional dependency with NOT condition in select."""
        ra = "fd_{a, b} \\select_{not(a = 1)} alpha;"
        expected = [r"\Tree[.$\sigma_{\neg (a \eq 1)} (alpha) : a \rightarrow b$ ]"]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)

    def test_multiple_functional_dependencies(self):
        """Test multiple functional dependencies in one statement."""
        ra = "fd_{a, b} \\select_{a = 1} alpha; fd_{c, d} \\select_{c > 0} beta;"
        expected = [
            r"\Tree[.$\sigma_{(a \eq 1)} (alpha) : a \rightarrow b$ ]",
            r"\Tree[.$\sigma_{(c \gt 0)} (beta) : c \rightarrow d$ ]",
        ]
        actual = self.translate(ra)
        self.assertEqual(expected, actual)


class TestDependencyLatexTranslation:
    """Test cases for LaTeX translation of dependency grammar statements."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rapt = Rapt(grammar="Dependency Grammar")
        self.schema = {"R": ["a", "b", "c"], "S": ["x", "y"], "T": ["id", "name"]}

    def test_primary_key_latex_translation(self):
        """Test LaTeX translation of primary key dependencies."""
        # Test single attribute primary key
        latex = self.rapt.to_qtree("pk_{a} R;", self.schema)
        assert len(latex) == 1
        assert "\\text{PK}(r) \\eq {a}" in latex[0]
        assert "\\Tree" in latex[0]

        # Test multiple attributes primary key
        latex = self.rapt.to_qtree("pk_{a, b} R;", self.schema)
        assert len(latex) == 1
        assert "\\text{PK}(r) \\eq {a,\\,b}" in latex[0]

    def test_multivalued_dependency_latex_translation(self):
        """Test LaTeX translation of multivalued dependencies."""
        # Test simple multivalued dependency
        latex = self.rapt.to_qtree("mvd_{a, b} R;", self.schema)
        assert len(latex) == 1
        assert "r : a \\twoheadrightarrow b" in latex[0]
        assert "\\Tree" in latex[0]

    def test_multivalued_dependency_with_select_latex_translation(self):
        """Test LaTeX translation of multivalued dependencies with select conditions."""
        latex = self.rapt.to_qtree("mvd_{a, b} \\select_{a = 1} R;", self.schema)
        assert len(latex) == 1
        assert "\\sigma_{(a \\eq 1)} (r) : a \\twoheadrightarrow b" in latex[0]
        assert "\\Tree" in latex[0]

    def test_inclusion_equivalence_latex_translation(self):
        """Test LaTeX translation of inclusion equivalence dependencies."""
        # Test simple inclusion equivalence
        latex = self.rapt.to_qtree("inc=_{a, b} (R, S);", self.schema)
        assert len(latex) == 1
        assert "r[a] \\equiv s[b]" in latex[0]
        assert "\\Tree" in latex[0]

    def test_inclusion_equivalence_with_select_latex_translation(self):
        """Test LaTeX translation of inclusion equivalence dependencies with select clauses."""
        # Test with select on left
        latex = self.rapt.to_qtree("inc=_{a, b} (\\select_{a = 1} R, S);", self.schema)
        assert len(latex) == 1
        assert "\\sigma_{(a \\eq 1)} (r)[a] \\equiv s[b]" in latex[0]
        assert "\\Tree" in latex[0]

        # Test with select on both sides
        latex = self.rapt.to_qtree("inc=_{a, b} (\\select_{a = 1} R, \\select_{x > 0} S);", self.schema)
        assert len(latex) == 1
        assert "\\sigma_{(a \\eq 1)} (r)[a] \\equiv \\sigma_{(x \\gt 0)} (s)[b]" in latex[0]
        assert "\\Tree" in latex[0]

    def test_inclusion_subsumption_latex_translation(self):
        """Test LaTeX translation of inclusion subsumption dependencies."""
        # Test simple inclusion subsumption
        latex = self.rapt.to_qtree("inc⊆_{a, b} (R, S);", self.schema)
        assert len(latex) == 1
        assert "r[a] \\subseteq s[b]" in latex[0]
        assert "\\Tree" in latex[0]

    def test_inclusion_subsumption_with_select_latex_translation(self):
        """Test LaTeX translation of inclusion subsumption dependencies with select clauses."""
        # Test with select on left
        latex = self.rapt.to_qtree("inc⊆_{a, b} (\\select_{a = 1} R, S);", self.schema)
        assert len(latex) == 1
        assert "\\sigma_{(a \\eq 1)} (r)[a] \\subseteq s[b]" in latex[0]
        assert "\\Tree" in latex[0]

    def test_multiple_dependency_statements_latex_translation(self):
        """Test LaTeX translation of multiple dependency statements."""
        latex = self.rapt.to_qtree(
            "pk_{a} R; mvd_{x, y} S; inc=_{a, b} (R, S); inc⊆_{x, y} (S, T);",
            self.schema,
        )
        assert len(latex) == 4

        # Check first statement (primary key)
        assert "\\text{PK}(r) \\eq {a}" in latex[0]

        # Check second statement (multivalued dependency)
        assert "s : x \\twoheadrightarrow y" in latex[1]

        # Check third statement (inclusion equivalence)
        assert "r[a] \\equiv s[b]" in latex[2]

        # Check fourth statement (inclusion subsumption)
        assert "s[x] \\subseteq t[y]" in latex[3]

    def test_latex_structure_consistency(self):
        """Test that LaTeX output has consistent structure."""
        test_cases = [
            "pk_{a, b} R;",
            "mvd_{x, y} S;",
            "inc=_{a, b} (R, S);",
            "inc⊆_{x, y} (S, T);",
        ]

        for test_case in test_cases:
            latex = self.rapt.to_qtree(test_case, self.schema)
            assert len(latex) == 1
            assert latex[0].startswith("\\Tree")
            assert latex[0].endswith(" ]")
            # Check for appropriate operators based on dependency type
            if "inc=" in test_case or "inc⊆" in test_case:
                assert "\\equiv" in latex[0] or "\\subseteq" in latex[0]
            elif "mvd" in test_case:
                assert "\\twoheadrightarrow" in latex[0]
            else:
                assert "\\text{" in latex[0]

    def test_latex_operators_mapping(self):
        """Test that correct LaTeX operators are used for each dependency type."""
        test_mappings = [
            ("pk_{a} R;", "\\text{PK}"),
            ("mvd_{a, b} R;", "\\twoheadrightarrow"),
            ("inc=_{a, b} (R, S);", "\\equiv"),
            ("inc⊆_{a, b} (R, S);", "\\subseteq"),
        ]

        for test_case, expected_operator in test_mappings:
            latex = self.rapt.to_qtree(test_case, self.schema)
            assert expected_operator in latex[0]

    def test_latex_attributes_formatting(self):
        """Test that attributes are properly formatted in LaTeX output."""
        # Test single attribute
        latex = self.rapt.to_qtree("pk_{a} R;", self.schema)
        assert "\\eq {a}" in latex[0]

        # Test multiple attributes
        latex = self.rapt.to_qtree("pk_{a, b, c} R;", self.schema)
        assert "\\eq {a,\\,b,\\,c}" in latex[0]

    def test_latex_relation_names_formatting(self):
        """Test that relation names are properly formatted in LaTeX output."""
        # Test single relation
        latex = self.rapt.to_qtree("pk_{a} R;", self.schema)
        assert "(r)" in latex[0]

        # Test inclusion dependencies with new format
        latex = self.rapt.to_qtree("inc=_{a, b} (R, S);", self.schema)
        assert "r[a]" in latex[0] and "s[b]" in latex[0]

        latex = self.rapt.to_qtree("inc⊆_{x, y} (S, T);", self.schema)
        assert "s[x]" in latex[0] and "t[y]" in latex[0]

    def test_latex_translation_with_different_schemas(self):
        """Test LaTeX translation with different schema configurations."""
        schema1 = {"Users": ["id", "name", "email"]}
        schema2 = {
            "Products": ["product_id", "name", "price"],
            "Orders": ["order_id", "customer_id"],
        }

        # Test with schema1
        latex1 = self.rapt.to_qtree("pk_{id} Users;", schema1)
        assert "\\text{PK}(users) \\eq {id}" in latex1[0]

        # Test with schema2
        latex2 = self.rapt.to_qtree("inc=_{id, name} (Products, Orders);", schema2)
        assert "products[id] \\equiv orders[name]" in latex2[0]

    def test_latex_translation_error_handling(self):
        """Test LaTeX translation error handling."""
        # Test with invalid syntax
        with pytest.raises(Exception):
            self.rapt.to_qtree("invalid syntax", self.schema)

        # Test with empty input
        with pytest.raises(Exception):
            self.rapt.to_qtree("", self.schema)

    def test_latex_translation_consistency_across_runs(self):
        """Test that LaTeX translation is consistent across multiple runs."""
        test_case = "pk_{a, b} R; mvd_{x, y} S;"

        # Run multiple times
        latex1 = self.rapt.to_qtree(test_case, self.schema)
        latex2 = self.rapt.to_qtree(test_case, self.schema)

        assert latex1 == latex2
        assert len(latex1) == 2
        assert len(latex2) == 2


class TestDependencyLatexTranslationIntegration:
    """Integration tests for dependency LaTeX translation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.grammar = DependencyGrammar()
        self.schema = {"R": ["a", "b", "c"], "S": ["x", "y"], "T": ["id", "name"]}
        self.builder = TreeBRD(self.grammar)

    def test_direct_grammar_latex_translation(self):
        """Test LaTeX translation using grammar directly."""
        from rapt2.transformers.qtree import qtree_translator

        # Parse dependency statements
        trees = self.builder.build("pk_{a, b} R;", self.schema)
        assert len(trees) == 1

        # Translate to LaTeX
        latex = qtree_translator.translate(list(trees))
        assert len(latex) == 1
        assert "\\text{PK}(r) \\eq {a,\\,b}" in latex[0]

    def test_multiple_dependency_types_latex_translation(self):
        """Test LaTeX translation of all dependency types in one go."""
        from rapt2.transformers.qtree import qtree_translator

        test_input = "pk_{a} R; mvd_{x, y} S; inc=_{a, b} (R, S); inc⊆_{x, y} (S, T);"
        trees = self.builder.build(test_input, self.schema)
        assert len(trees) == 4

        latex = qtree_translator.translate(list(trees))
        assert len(latex) == 4

        # Check each dependency type is properly translated
        expected_operators = [
            "\\text{PK}",
            "\\twoheadrightarrow",
            "\\equiv",
            "\\subseteq",
        ]
        for i, expected_op in enumerate(expected_operators):
            assert expected_op in latex[i]
