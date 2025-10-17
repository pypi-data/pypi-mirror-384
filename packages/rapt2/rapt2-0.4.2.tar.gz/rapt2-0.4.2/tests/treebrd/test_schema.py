from unittest import TestCase

from rapt2.treebrd.errors import RelationReferenceError
from rapt2.treebrd.schema import Schema
from rapt2.treebrd.node import DefinitionNode


class TestSchema(TestCase):
    def test_contains_when_empty(self):
        self.assertFalse(Schema({}).contains("relation"))

    def test_contains_when_false(self):
        self.assertFalse(Schema({"another_relation": []}).contains("relation"))

    def test_contains_when_true(self):
        self.assertTrue(Schema({"relation": []}).contains("relation"))

    def test_to_dict(self):
        expected = {"alpha": ["a1"], "beta": ["b1"]}
        actual = Schema(expected).to_dict()
        self.assertNotEqual(id(expected), id(actual))
        self.assertEqual(expected, actual)

    def test_get_attributes(self):
        raw = {"alpha": ["a1"], "beta": ["b1"]}
        expected = ["a1"]
        actual = Schema(raw).get_attributes("alpha")
        self.assertNotEqual(id(expected), id(raw["alpha"]))
        self.assertEqual(expected, actual)

    def test_add(self):
        schema = Schema({"alpha": ["a1"]})
        schema.add("beta", ["b1"])
        self.assertTrue(schema.contains("beta"))
        self.assertEqual(["b1"], schema.get_attributes("beta"))

    def test_exception_when_name_conflicts(self):
        schema = Schema({"alpha": ["a1"]})
        self.assertRaises(RelationReferenceError, schema.add, "alpha", [])

    def test_definition_node_adds_to_schema(self):
        """Test that DefinitionNode adds its attributes to the schema."""
        schema = Schema({"existing": ["attr1"]})
        
        # Create a definition node
        definition = DefinitionNode("new_relation", ["attr1", "attr2", "attr3"], schema)
        
        # Verify the relation was added to the schema
        self.assertTrue(schema.contains("new_relation"))
        self.assertEqual(["attr1", "attr2", "attr3"], schema.get_attributes("new_relation"))
        
        # Verify the existing relation is still there
        self.assertTrue(schema.contains("existing"))
        self.assertEqual(["attr1"], schema.get_attributes("existing"))

    def test_definition_node_raises_error_on_duplicate_name(self):
        """Test that DefinitionNode raises error when trying to define a relation that already exists."""
        schema = Schema({"existing": ["attr1"]})
        
        # This should raise a RelationReferenceError
        self.assertRaises(RelationReferenceError, DefinitionNode, "existing", ["attr2", "attr3"], schema)
