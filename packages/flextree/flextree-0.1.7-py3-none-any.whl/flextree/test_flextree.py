import unittest
import json
import tempfile
import os
from flextree import TreeNode, Tree, draw_tree
from io import StringIO
import sys


class TestTreeNode(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.root = TreeNode("root", "root content")
        self.child1 = TreeNode("child1", "content1")
        self.child2 = TreeNode("child2", "content2")
        self.grandchild = TreeNode("grandchild", "gc content")
    
    def test_node_creation(self):
        """Test TreeNode creation."""
        node = TreeNode("test", "test content")
        self.assertEqual(node.name, "test")
        self.assertEqual(node.content, "test content")
        self.assertEqual(len(node.children), 0)
        self.assertIsNone(node.parent)
    
    def test_add_child(self):
        """Test adding children to a node."""
        self.root.add_child(self.child1)
        self.assertEqual(len(self.root.children), 1)
        self.assertEqual(self.child1.parent, self.root)
        self.assertIn(self.child1, self.root.children)
    
    def test_remove_child_by_node(self):
        """Test removing child by node reference."""
        self.root.add_child(self.child1)
        self.root.add_child(self.child2)
        self.root.remove_child(self.child1)
        self.assertEqual(len(self.root.children), 1)
        self.assertNotIn(self.child1, self.root.children)
        self.assertIn(self.child2, self.root.children)
    
    def test_remove_child_by_name(self):
        """Test removing child by name."""
        self.root.add_child(self.child1)
        self.root.add_child(self.child2)
        self.root.remove_child("child1")
        self.assertEqual(len(self.root.children), 1)
        self.assertEqual(self.root.children[0].name, "child2")
    
    def test_remove_child_by_index(self):
        """Test removing child by index."""
        self.root.add_child(self.child1)
        self.root.add_child(self.child2)
        self.root.remove_child(0)
        self.assertEqual(len(self.root.children), 1)
        self.assertEqual(self.root.children[0].name, "child2")
    
    def test_get_child_by_name(self):
        """Test getting child by name."""
        self.root.add_child(self.child1)
        found_child = self.root.get_child("child1")
        self.assertEqual(found_child, self.child1)
        
        not_found = self.root.get_child("nonexistent")
        self.assertIsNone(not_found)
    
    def test_get_child_by_index(self):
        """Test getting child by index."""
        self.root.add_child(self.child1)
        self.root.add_child(self.child2)
        
        # Test positive indices
        found_child = self.root.get_child(0)
        self.assertEqual(found_child, self.child1)
        
        found_child = self.root.get_child(1)
        self.assertEqual(found_child, self.child2)
        
        # Test negative indices
        found_child = self.root.get_child(-1)
        self.assertEqual(found_child, self.child2)  # Last child
        
        found_child = self.root.get_child(-2)
        self.assertEqual(found_child, self.child1)  # Second to last
        
        # Test out of bounds positive index
        out_of_bounds = self.root.get_child(5)
        self.assertIsNone(out_of_bounds)
        
        # Test out of bounds negative index
        with self.assertRaises(IndexError):
            self.root.get_child(-5)
        
        # Test empty children list
        empty_node = TreeNode("empty", "no children")
        self.assertIsNone(empty_node.get_child(0))
        with self.assertRaises(IndexError):
            empty_node.get_child(-1)
    
    def test_set_content(self):
        """Test setting node content."""
        self.root.set_content("new content")
        self.assertEqual(self.root.content, "new content")
    
    def test_get_subtree(self):
        """Test finding subtree by name."""
        self.root.add_child(self.child1)
        self.child1.add_child(self.grandchild)
        
        # Find root
        found = self.root.get_subtree("root")
        self.assertEqual(found, self.root)
        
        # Find child
        found = self.root.get_subtree("child1")
        self.assertEqual(found, self.child1)
        
        # Find grandchild
        found = self.root.get_subtree("grandchild")
        self.assertEqual(found, self.grandchild)
        
        # Not found
        found = self.root.get_subtree("nonexistent")
        self.assertIsNone(found)
    
    def test_to_dict(self):
        """Test converting node to dictionary."""
        self.root.add_child(self.child1)
        result = self.root.to_dict()
        
        expected = {
            'name': 'root',
            'content': 'root content',
            'children': [{
                'name': 'child1',
                'content': 'content1',
                'children': []
            }]
        }
        self.assertEqual(result, expected)
    
    def test_from_dict(self):
        """Test creating node from dictionary."""
        data = {
            'name': 'test_root',
            'content': 'test content',
            'children': [{
                'name': 'test_child',
                'content': 'child content',
                'children': []
            }]
        }
        
        node = TreeNode.from_dict(data)
        self.assertEqual(node.name, 'test_root')
        self.assertEqual(node.content, 'test content')
        self.assertEqual(len(node.children), 1)
        self.assertEqual(node.children[0].name, 'test_child')
        self.assertEqual(node.children[0].parent, node)
    
    def test_max_depth(self):
        """Test calculating maximum depth."""
        # Single node
        self.assertEqual(self.root.max_depth(), 1)
        
        # Two levels
        self.root.add_child(self.child1)
        self.assertEqual(self.root.max_depth(), 2)
        
        # Three levels
        self.child1.add_child(self.grandchild)
        self.assertEqual(self.root.max_depth(), 3)
    
    def test_max_width(self):
        """Test calculating maximum width."""
        # Single node
        self.assertEqual(self.root.max_width(), 1)
        
        # Two children
        self.root.add_child(self.child1)
        self.root.add_child(self.child2)
        self.assertEqual(self.root.max_width(), 2)
        
        # Child with more children
        child3 = TreeNode("child3", "content3")
        child4 = TreeNode("child4", "content4")
        self.child1.add_child(child3)
        self.child1.add_child(child4)
        self.child1.add_child(self.grandchild)
        self.assertEqual(self.root.max_width(), 3)  # child1 has 3 children

    def test_count(self):
        """Test counting total nodes in subtree."""
        # Single node
        self.assertEqual(self.root.count(), 1)
        
        # Two levels
        self.root.add_child(self.child1)
        self.assertEqual(self.root.count(), 2)
        self.assertEqual(self.child1.count(), 1)  # child1 only counts itself
        
        # Three levels
        self.child1.add_child(self.grandchild)
        self.assertEqual(self.root.count(), 3)
        self.assertEqual(self.child1.count(), 2)  # child1 + grandchild
        self.assertEqual(self.grandchild.count(), 1)  # grandchild only
        
        # Multiple children
        self.root.add_child(self.child2)
        self.assertEqual(self.root.count(), 4)  # root + child1 + grandchild + child2
        
        # Add more grandchildren
        gc2 = TreeNode("gc2", "content")
        gc3 = TreeNode("gc3", "content")
        self.child2.add_child(gc2)
        self.child2.add_child(gc3)
        self.assertEqual(self.root.count(), 6)  # root + child1 + grandchild + child2 + gc2 + gc3
        self.assertEqual(self.child2.count(), 3)  # child2 + gc2 + gc3

    def test_summary(self):
        """Test node summary generation."""
        summary = self.root.summary()
        self.assertIn("root:", summary)
        self.assertIn("root content", summary)
        self.assertIn("Max Depth:", summary)
        self.assertIn("Max Width:", summary)
    
    def test_summary_long_content(self):
        """Test summary with long content gets truncated."""
        long_content = "a" * 50
        node = TreeNode("test", long_content)
        summary = node.summary()
        self.assertIn("...", summary)
    
    def test_repr(self):
        """Test string representation."""
        self.root.add_child(self.child1)
        repr_str = repr(self.root)
        self.assertIn("TreeNode", repr_str)
        self.assertIn("name=root", repr_str)
        self.assertIn("children=1", repr_str)

    def test_draw(self):
        """Test that draw method produces output without errors."""
        self.root.add_child(self.child1)
        self.child1.add_child(self.grandchild)
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            self.root.draw()
            output = captured_output.getvalue()
            
            # Check that output contains expected elements
            self.assertIn("root:", output)
            self.assertIn("child1:", output)
            self.assertIn("grandchild:", output)
            self.assertIn("gc content", output)
            
        finally:
            sys.stdout = old_stdout


class TestTree(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = TreeNode("root", "root content")
        self.tree = Tree(self.root)
    
    def test_tree_creation(self):
        """Test Tree creation."""
        self.assertEqual(self.tree.root, self.root)
    
    def test_insert(self):
        """Test inserting nodes into the tree."""
        child = TreeNode("child", "child content")
        self.tree.insert("root", child)
        
        self.assertEqual(len(self.root.children), 1)
        self.assertEqual(self.root.children[0], child)
        self.assertEqual(child.parent, self.root)
    
    def test_insert_nonexistent_parent(self):
        """Test inserting with nonexistent parent."""
        child = TreeNode("child", "child content")
        self.tree.insert("nonexistent", child)
        
        # Should not add the child
        self.assertEqual(len(self.root.children), 0)
    
    def test_delete(self):
        """Test deleting nodes from the tree."""
        child = TreeNode("child", "child content")
        self.root.add_child(child)
        
        self.tree.delete("child")
        self.assertEqual(len(self.root.children), 0)
    
    def test_delete_root(self):
        """Test deleting root node (should not work)."""
        original_children = len(self.root.children)
        self.tree.delete("root")
        # Root should still exist (can't delete node without parent)
        self.assertEqual(len(self.root.children), original_children)
    
    def test_alter(self):
        """Test altering node content."""
        self.tree.alter("root", "new root content")
        self.assertEqual(self.root.content, "new root content")
    
    def test_alter_nonexistent(self):
        """Test altering nonexistent node."""
        original_content = self.root.content
        self.tree.alter("nonexistent", "new content")
        self.assertEqual(self.root.content, original_content)
    
    def test_get_by_name(self):
        """Test getting subtree by name."""
        child = TreeNode("child", "child content")
        self.root.add_child(child)
        
        subtree = self.tree.get("child")
        self.assertIsInstance(subtree, Tree)
        self.assertEqual(subtree.root, child)
    
    def test_get_by_index(self):
        """Test getting subtree by index."""
        child = TreeNode("child", "child content")
        self.root.add_child(child)
        
        subtree = self.tree.get(0)
        self.assertIsInstance(subtree, Tree)
        self.assertEqual(subtree.root, child)
    
    def test_get_nonexistent(self):
        """Test getting nonexistent node."""
        result = self.tree.get("nonexistent")
        self.assertIsNone(result)
    
    def test_summary(self):
        """Test tree summary."""
        summary = self.tree.summary()
        self.assertIn("root:", summary)
        self.assertIn("Max Depth:", summary)
        self.assertIn("Max Width:", summary)
    
    def test_repr(self):
        """Test tree string representation."""
        repr_str = repr(self.tree)
        self.assertIn("Tree", repr_str)
        self.assertIn("root=", repr_str)
        self.assertIn("depth=", repr_str)
        self.assertIn("width=", repr_str)
    
    def test_max_depth(self):
        """Test tree max depth calculation."""
        child = TreeNode("child", "content")
        grandchild = TreeNode("grandchild", "content")
        
        self.assertEqual(self.tree.max_depth(), 1)
        
        self.root.add_child(child)
        self.assertEqual(self.tree.max_depth(), 2)
        
        child.add_child(grandchild)
        self.assertEqual(self.tree.max_depth(), 3)
    
    def test_max_width(self):
        """Test tree max width calculation."""
        child1 = TreeNode("child1", "content1")
        child2 = TreeNode("child2", "content2")
        
        self.assertEqual(self.tree.max_width(), 1)
        
        self.root.add_child(child1)
        self.root.add_child(child2)
        self.assertEqual(self.tree.max_width(), 2)

    def test_count(self):
        """Test counting total nodes in tree."""
        # Single node (root only)
        self.assertEqual(self.tree.count(), 1)
        
        # Add children
        child1 = TreeNode("child1", "content1")
        child2 = TreeNode("child2", "content2")
        self.tree.insert("root", child1)
        self.assertEqual(self.tree.count(), 2)
        
        self.tree.insert("root", child2)
        self.assertEqual(self.tree.count(), 3)
        
        # Add grandchildren
        grandchild1 = TreeNode("grandchild1", "gc1")
        grandchild2 = TreeNode("grandchild2", "gc2")
        self.tree.insert("child1", grandchild1)
        self.tree.insert("child2", grandchild2)
        self.assertEqual(self.tree.count(), 5)  # root + 2 children + 2 grandchildren
        
        # Test that count matches root.count()
        self.assertEqual(self.tree.count(), self.tree.root.count())
        
        # Delete a node and verify count decreases
        self.tree.delete("grandchild1")
        self.assertEqual(self.tree.count(), 4)  # Should be 4 after deletion

    def test_getitem_by_name(self):
        """Test Tree getitem access by name."""
        child1 = TreeNode("child1", "content1")
        child2 = TreeNode("child2", "content2")
        self.tree.insert("root", child1)
        self.tree.insert("root", child2)
        
        # Test string access (by name) - should return Tree object
        found_subtree = self.tree["child1"]
        self.assertIsInstance(found_subtree, Tree)
        self.assertEqual(found_subtree.root, child1)
        
        # Test non-existent name
        not_found = self.tree["nonexistent"]
        self.assertIsNone(not_found)
        
        # Test deep search
        grandchild = TreeNode("grandchild", "gc content")
        self.tree.insert("child1", grandchild)
        found_deep = self.tree["grandchild"]
        self.assertIsInstance(found_deep, Tree)
        self.assertEqual(found_deep.root, grandchild)
    
    def test_getitem_by_index(self):
        """Test Tree getitem access by index."""
        child1 = TreeNode("child1", "content1")
        child2 = TreeNode("child2", "content2")
        self.tree.insert("root", child1)
        self.tree.insert("root", child2)
        
        # Test integer access (by index) - should return Tree object
        first_child_tree = self.tree[0]
        self.assertIsInstance(first_child_tree, Tree)
        self.assertEqual(first_child_tree.root, child1)
        
        second_child_tree = self.tree[1]
        self.assertIsInstance(second_child_tree, Tree)
        self.assertEqual(second_child_tree.root, child2)
        
        # Test out of bounds index
        out_of_bounds = self.tree[5]
        self.assertIsNone(out_of_bounds)
    
    def test_getitem_by_slice(self):
        """Test Tree getitem access by slice."""
        child1 = TreeNode("child1", "content1")
        child2 = TreeNode("child2", "content2")
        child3 = TreeNode("child3", "content3")
        self.tree.insert("root", child1)
        self.tree.insert("root", child2)
        self.tree.insert("root", child3)
        
        # Test slice access - should return list of Tree objects
        first_two = self.tree[0:2]
        self.assertIsInstance(first_two, list)
        self.assertEqual(len(first_two), 2)
        self.assertIsInstance(first_two[0], Tree)
        self.assertIsInstance(first_two[1], Tree)
        self.assertEqual(first_two[0].root, child1)
        self.assertEqual(first_two[1].root, child2)
        
        # Test slice all
        all_children = self.tree[:]
        self.assertEqual(len(all_children), 3)
        
        # Test negative slice
        last_two = self.tree[-2:]
        self.assertEqual(len(last_two), 2)
        self.assertEqual(last_two[0].root, child2)
        self.assertEqual(last_two[1].root, child3)
    
    def test_getitem_by_list(self):
        """Test Tree getitem access by list of keys."""
        child1 = TreeNode("child1", "content1")
        child2 = TreeNode("child2", "content2")
        child3 = TreeNode("child3", "content3")
        self.tree.insert("root", child1)
        self.tree.insert("root", child2)
        self.tree.insert("root", child3)
        
        # Test list access with mixed key types - should return list of Tree objects
        selected = self.tree[["child1", "child3"]]
        self.assertIsInstance(selected, list)
        self.assertEqual(len(selected), 2)
        self.assertIsInstance(selected[0], Tree)
        self.assertIsInstance(selected[1], Tree)
        self.assertEqual(selected[0].root, child1)
        self.assertEqual(selected[1].root, child3)
    
    def test_getitem_chaining(self):
        """Test chaining getitem operations."""
        # Create nested structure
        engineering = TreeNode("engineering", "Engineering Dept")
        backend = TreeNode("backend", "Backend Team")
        frontend = TreeNode("frontend", "Frontend Team")
        
        self.tree.insert("root", engineering)
        self.tree.insert("engineering", backend)
        self.tree.insert("engineering", frontend)
        
        # Test chaining: get engineering dept, then get its first child
        eng_tree = self.tree["engineering"]
        self.assertIsNotNone(eng_tree)
        
        first_team = eng_tree[0]
        self.assertIsInstance(first_team, Tree)
        self.assertEqual(first_team.root, backend)
        
        # Test getting all teams under engineering
        all_teams = eng_tree[:]
        self.assertEqual(len(all_teams), 2)
        self.assertEqual(all_teams[0].root, backend)
        self.assertEqual(all_teams[1].root, frontend)
    
    def test_save_and_load_json(self):
        """Test saving and loading tree to/from JSON."""
        child = TreeNode("child", {"key": "value"})
        self.root.add_child(child)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            # Save
            self.tree.save_json(temp_file)
            
            # Load
            loaded_tree = Tree.load_json(temp_file)
            
            # Verify
            self.assertEqual(loaded_tree.root.name, self.root.name)
            self.assertEqual(loaded_tree.root.content, self.root.content)
            self.assertEqual(len(loaded_tree.root.children), 1)
            self.assertEqual(loaded_tree.root.children[0].name, "child")
            self.assertEqual(loaded_tree.root.children[0].content, {"key": "value"})
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_draw(self):
        """Test that draw method produces output without errors."""
        child = TreeNode("child", "child content")
        grandchild = TreeNode("grandchild", "gc content")
        self.root.add_child(child)
        child.add_child(grandchild)
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            self.tree.draw()
            output = captured_output.getvalue()
            
            # Check that output contains expected elements
            self.assertIn("root:", output)
            self.assertIn("child:", output)
            self.assertIn("grandchild:", output)
            self.assertIn("gc content", output)
            
        finally:
            sys.stdout = old_stdout
    
    def test_to_dict(self):
        """Test converting tree to dictionary."""
        child = TreeNode("child", "child content")
        self.root.add_child(child)
        
        tree_dict = self.tree.to_dict()
        expected_dict = {
            'name': 'root',
            'content': 'root content',
            'children': [{
                'name': 'child',
                'content': 'child content',
                'children': []
            }]
        }
        self.assertEqual(tree_dict, expected_dict)
    
    def test_from_dict(self):
        """Test creating tree from dictionary."""
        data = {
            'name': 'root',
            'content': 'root content',
            'children': [{
                'name': 'child',
                'content': 'child content',
                'children': []
            }]
        }
        
        tree = Tree.from_dict(data)
        self.assertEqual(tree.root.name, 'root')
        self.assertEqual(tree.root.content, 'root content')
        self.assertEqual(len(tree.root.children), 1)
        self.assertEqual(tree.root.children[0].name, 'child')
        self.assertEqual(tree.root.children[0].content, 'child content')

class TestDrawTree(unittest.TestCase):
    
    def test_draw_tree_output(self):
        """Test that draw_tree produces output without errors."""
        root = TreeNode("root", "root content")
        child1 = TreeNode("child1", "content1")
        child2 = TreeNode("child2", "content2")
        grandchild = TreeNode("grandchild", {"definition": "test definition"})
        
        root.add_child(child1)
        root.add_child(child2)
        child1.add_child(grandchild)
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            draw_tree(root)
            output = captured_output.getvalue()
            
            # Check that output contains expected elements
            self.assertIn("root:", output)
            self.assertIn("child1:", output)
            self.assertIn("child2:", output)
            self.assertIn("grandchild:", output)
            self.assertIn("test definition", output)
            
        finally:
            sys.stdout = old_stdout
    
    def test_draw_tree_custom_key(self):
        """Test draw_tree with custom key."""
        root = TreeNode("root", {"desc": "root description", "other": "ignored"})
        child = TreeNode("child", {"desc": "child description", "data": "more data"})
        root.add_child(child)
        
        # Test with custom key
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            draw_tree(root, key="desc")
            output = captured_output.getvalue()
            
            # Check that custom key content is displayed
            self.assertIn("root description", output)
            self.assertIn("child description", output)
            # Check that other dictionary content is not displayed
            self.assertNotIn("ignored", output)
            self.assertNotIn("more data", output)
            
        finally:
            sys.stdout = old_stdout
    
    def test_draw_tree_nonexistent_key(self):
        """Test draw_tree with nonexistent key shows full dict."""
        root = TreeNode("root", {"data": "some data", "value": 42})
        
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            draw_tree(root, key="nonexistent")
            output = captured_output.getvalue()
            
            # Should display the entire dictionary since key doesn't exist
            self.assertIn("{'data': 'some data', 'value': 42}", output)
            
        finally:
            sys.stdout = old_stdout
    
    def test_draw_tree_mixed_content_types(self):
        """Test draw_tree with mixed content types and custom key."""
        root = TreeNode("root", "string content")
        dict_child = TreeNode("dict_child", {"custom_key": "custom value", "other": "data"})
        string_child = TreeNode("string_child", "another string")
        none_child = TreeNode("none_child", None)
        
        root.add_child(dict_child)
        root.add_child(string_child)
        root.add_child(none_child)
        
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            draw_tree(root, key="custom_key")
            output = captured_output.getvalue()
            
            # String content should remain unchanged
            self.assertIn("string content", output)
            self.assertIn("another string", output)
            # Dict with custom key should show only that value
            self.assertIn("custom value", output)
            # Check that the full dictionary is not displayed (would contain 'other': 'data')
            self.assertNotIn("'other': 'data'", output)
            self.assertNotIn('"other": "data"', output)
            # None content should display as None
            self.assertIn("None", output)
            
        finally:
            sys.stdout = old_stdout
    
    def test_node_draw_method(self):
        """Test TreeNode.draw() method with custom key."""
        node = TreeNode("test", {"label": "test label", "extra": "ignored"})
        child = TreeNode("child", {"label": "child label"})
        node.add_child(child)
        
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            node.draw(key="label")
            output = captured_output.getvalue()
            
            self.assertIn("test label", output)
            self.assertIn("child label", output)
            self.assertNotIn("ignored", output)
            
        finally:
            sys.stdout = old_stdout
    
    def test_tree_draw_method(self):
        """Test Tree.draw() method with custom key."""
        root = TreeNode("root", {"title": "root title"})
        tree = Tree(root)
        child = TreeNode("child", {"title": "child title"})
        tree.insert("root", child)
        
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            tree.draw(key="title")
            output = captured_output.getvalue()
            
            self.assertIn("root title", output)
            self.assertIn("child title", output)
            
        finally:
            sys.stdout = old_stdout


if __name__ == '__main__':
    unittest.main()