import unittest
from src.nest_tree import tree


class TestTree(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.simple_dict = {
            "name": "John",
            "age": 30,
            "city": "New York"
        }
        
        self.nested_dict = {
            "user": {
                "name": "Alice",
                "details": {
                    "age": 25,
                    "location": "Boston"
                }
            },
            "settings": {
                "theme": "dark",
                "notifications": True
            }
        }
        
        self.simple_list = ["apple", "banana", "cherry"]
        
        self.nested_list = [
            ["a", "b"],
            ["c", "d", "e"],
            ["f"]
        ]
        
        self.mixed_structure = {
            "fruits": ["apple", "banana"],
            "vegetables": {
                "green": ["lettuce", "spinach"],
                "root": ["carrot", "potato"]
            },
            "count": 42
        }

    def test_simple_dict_no_leaf(self):
        """Test simple dictionary with leaf='none'."""
        result = tree(self.simple_dict, leaf="none", print_output=False, return_output=True)
        expected_lines = [
            "├── name",
            "├── age", 
            "└── city"
        ]
        for line in expected_lines:
            self.assertIn(line, result)

    def test_simple_dict_with_values(self):
        """Test simple dictionary with leaf='value'."""
        result = tree(self.simple_dict, leaf="value", print_output=False, return_output=True)
        self.assertIn("John", result)
        self.assertIn("30", result)
        self.assertIn("New York", result)

    def test_simple_dict_with_types(self):
        """Test simple dictionary with leaf='type'."""
        result = tree(self.simple_dict, leaf="type", print_output=False, return_output=True)
        self.assertIn("<class 'str'>", result)
        self.assertIn("<class 'int'>", result)

    def test_nested_dict(self):
        """Test nested dictionary structure."""
        result = tree(self.nested_dict, leaf="none", print_output=False, return_output=True)
        expected_lines = [
            "├── user",
            "│   ├── name",
            "│   └── details",
            "│       ├── age",
            "│       └── location",
            "└── settings",
            "    ├── theme",
            "    └── notifications"
        ]
        for line in expected_lines:
            self.assertIn(line, result)

    def test_simple_list(self):
        """Test simple list structure."""
        result = tree(self.simple_list, leaf="value", print_output=False, return_output=True)
        expected_lines = [
            "├── [0]",
            "│   └── apple",
            "├── [1]", 
            "│   └── banana",
            "└── [2]",
            "    └── cherry"
        ]
        for line in expected_lines:
            self.assertIn(line, result)

    def test_nested_list(self):
        """Test nested list structure."""
        result = tree(self.nested_list, leaf="none", print_output=False, return_output=True)
        expected_lines = [
            "├── [0]",
            "│   ├── [0]",
            "│   └── [1]",
            "├── [1]",
            "│   ├── [0]",
            "│   ├── [1]",
            "│   └── [2]",
            "└── [2]",
            "    └── [0]"
        ]
        for line in expected_lines:
            self.assertIn(line, result)

    def test_mixed_structure(self):
        """Test mixed dict/list structure."""
        result = tree(self.mixed_structure, leaf="none", print_output=False, return_output=True)
        self.assertIn("fruits", result)
        self.assertIn("vegetables", result)
        self.assertIn("green", result)
        self.assertIn("root", result)
        self.assertIn("[0]", result)
        self.assertIn("[1]", result)

    def test_level_limit(self):
        """Test level limiting functionality."""
        result = tree(self.nested_dict, leaf="none", level=1, print_output=False, return_output=True)
        # Should only show first level
        self.assertIn("user", result)
        self.assertIn("settings", result)
        # Should not show second level
        self.assertNotIn("name", result)
        self.assertNotIn("details", result)
        self.assertNotIn("theme", result)

    def test_level_limit_zero(self):
        """Test level limit of 0."""
        result = tree(self.simple_dict, leaf="none", level=0, print_output=False, return_output=True)
        # Should show nothing since we stop at depth 0
        self.assertEqual(result.strip(), "")

    def test_empty_dict(self):
        """Test empty dictionary."""
        result = tree({}, leaf="none", print_output=False, return_output=True)
        self.assertEqual(result.strip(), "")

    def test_empty_list(self):
        """Test empty list."""
        result = tree([], leaf="none", print_output=False, return_output=True)
        self.assertEqual(result.strip(), "")

    def test_single_value_dict(self):
        """Test dictionary with single key-value pair."""
        data = {"key": "value"}
        result = tree(data, leaf="value", print_output=False, return_output=True)
        expected_lines = [
            "└── key",
            "    └── value"
        ]
        for line in expected_lines:
            self.assertIn(line, result)

    def test_single_item_list(self):
        """Test list with single item."""
        data = ["single"]
        result = tree(data, leaf="value", print_output=False, return_output=True)
        expected_lines = [
            "└── [0]",
            "    └── single"
        ]
        for line in expected_lines:
            self.assertIn(line, result)

    def test_print_output_parameter(self):
        """Test that print_output parameter works correctly."""
        # We can't easily test actual printing, but we can verify the function
        # returns the expected string regardless of print_output value
        result_with_print = tree(self.simple_dict, leaf="none", print_output=True, return_output=True)
        result_without_print = tree(self.simple_dict, leaf="none", print_output=False, return_output=True)
        self.assertEqual(result_with_print, result_without_print)

    def test_different_data_types_in_leaves(self):
        """Test handling of different data types in leaf nodes."""
        data = {
            "string": "hello",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "none": None
        }
        result = tree(data, leaf="type", print_output=False, return_output=True)
        self.assertIn("<class 'str'>", result)
        self.assertIn("<class 'int'>", result)
        self.assertIn("<class 'float'>", result)
        self.assertIn("<class 'bool'>", result)
        self.assertIn("<class 'NoneType'>", result)

    def test_deeply_nested_structure(self):
        """Test deeply nested structure."""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": "deep_value"
                    }
                }
            }
        }
        result = tree(data, leaf="value", print_output=False, return_output=True)
        self.assertIn("level1", result)
        self.assertIn("level2", result)
        self.assertIn("level3", result)
        self.assertIn("level4", result)
        self.assertIn("deep_value", result)

    def test_return_output_parameter(self):
        """Test that return_output parameter works correctly."""
        data = {"key": "value"}
        
        # Test return_output=False (default) - should return None
        result_no_return = tree(data, print_output=False, return_output=False)
        self.assertIsNone(result_no_return)
        
        # Test return_output=True - should return string
        result_with_return = tree(data, print_output=False, return_output=True)
        self.assertIsInstance(result_with_return, str)
        self.assertIn("key", result_with_return)
        
        # Test default behavior (return_output=False by default)
        result_default = tree(data, print_output=False)
        self.assertIsNone(result_default)


if __name__ == '__main__':
    unittest.main()