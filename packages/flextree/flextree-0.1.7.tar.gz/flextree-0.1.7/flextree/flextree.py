import json
from typing import Any, Optional, List, Dict, Union

class TreeNode:
    """
    A node in a tree data structure.
    
    Each TreeNode represents a single node in a hierarchical tree structure.
    It can contain any type of content and maintains relationships with its
    parent and children nodes.
    
    Attributes:
        name (str): The unique identifier/name for this node
        content (Any): The data/content stored in this node
        children (List[TreeNode]): List of child nodes
        parent (Optional[TreeNode]): Reference to parent node, None for root
        
    Example:
        >>> root = TreeNode("root", "root content")
        >>> child = TreeNode("child1", {"key": "value"})
        >>> root.add_child(child)
        >>> print(root.children[0].name)
        child1
    """
    def __init__(self, name: str, content: Any = None):
        """
        Initialize a new TreeNode.
        
        Args:
            name (str): The name/identifier for this node
            content (Any, optional): The content to store in this node. 
                                   Can be any Python object. Defaults to None.
        """
        self.name = name
        self.content = content
        self.children: List['TreeNode'] = []
        self.parent: Optional['TreeNode'] = None

    def add_child(self, child: 'TreeNode'):
        """
        Add a child node to this node.
        
        This method establishes a parent-child relationship by setting
        the child's parent reference and adding the child to this node's
        children list.
        
        Args:
            child (TreeNode): The node to add as a child
            
        Example:
            >>> parent = TreeNode("parent")
            >>> child = TreeNode("child")
            >>> parent.add_child(child)
            >>> child.parent == parent
            True
        """
        child.parent = self
        self.children.append(child)

    def remove_child(self, child: Union['TreeNode', str, int]):
        """
        Remove a child node from this node.
        
        This method can remove a child by node reference, by name, or by index.
        The parent reference of the removed child is not modified.
        
        Args:
            child (Union[TreeNode, str, int]): The child to remove. Can be:
                - TreeNode: The actual node object to remove
                - str: The name of the child node to remove
                - int: The index of the child to remove (0-based)
                
        Example:
            >>> parent = TreeNode("parent")
            >>> child1 = TreeNode("child1")
            >>> child2 = TreeNode("child2")
            >>> parent.add_child(child1)
            >>> parent.add_child(child2)
            >>> parent.remove_child("child1")  # Remove by name
            >>> parent.remove_child(0)         # Remove by index
        """
        if isinstance(child, TreeNode):
            self.children.remove(child)
        elif isinstance(child, str):
            self.children = [c for c in self.children if c.name != child]
        elif isinstance(child, int):
            if 0 <= child < len(self.children):
                del self.children[child]

    def get_child(self, key: Union[str, int]) -> Optional['TreeNode']:
        """
        Retrieve a direct child node by name or index.
        
        This method only searches among direct children, not descendants.
        For deep searching, use get_subtree() instead.
        
        Args:
            key (Union[str, int]): The identifier for the child. Can be:
                - str: The name of the child node
                - int: The index of the child (0-based)
                
        Returns:
            Optional[TreeNode]: The found child node, or None if not found
            
        Example:
            >>> parent = TreeNode("parent")
            >>> child = TreeNode("child")
            >>> parent.add_child(child)
            >>> found = parent.get_child("child")
            >>> found == child
            True
        """
        if isinstance(key, str):
            for child in self.children:
                if child.name == key:
                    return child
        elif isinstance(key, int):
            if 0 <= key < len(self.children):
                return self.children[key]
            elif key < 0:
                idx = len(self.children) + key
                if 0 <= idx < len(self.children):
                    return self.children[idx]
                else:
                    raise IndexError("Child index out of range")
        return None

    def set_content(self, content: Any):
        """
        Set or update the content of this node.
        
        Args:
            content (Any): The new content to store in this node.
                          Can be any Python object.
                          
        Example:
            >>> node = TreeNode("test", "old content")
            >>> node.set_content({"new": "content"})
            >>> node.content
            {'new': 'content'}
        """
        self.content = content

    def get_subtree(self, name: str) -> Optional['TreeNode']:
        """
        Find and return a node by name anywhere in the subtree.
        
        This method performs a depth-first search starting from this node
        to find a node with the specified name. It searches through all
        descendants, not just direct children.
        
        Args:
            name (str): The name of the node to find
            
        Returns:
            Optional[TreeNode]: The found node, or None if not found
            
        Example:
            >>> root = TreeNode("root")
            >>> child = TreeNode("child")
            >>> grandchild = TreeNode("grandchild")
            >>> root.add_child(child)
            >>> child.add_child(grandchild)
            >>> found = root.get_subtree("grandchild")
            >>> found == grandchild
            True
        """
        if self.name == name:
            return self
        for child in self.children:
            result = child.get_subtree(name)
            if result:
                return result
        return None

    def to_dict(self) -> Dict:
        """
        Convert this node and its entire subtree to a dictionary.
        
        This method recursively converts the node and all its descendants
        into a nested dictionary structure suitable for JSON serialization.
        
        Returns:
            Dict: A dictionary representation of the node with keys:
                - 'name': The node's name
                - 'content': The node's content  
                - 'children': List of child dictionaries
                
        Example:
            >>> root = TreeNode("root", "content")
            >>> child = TreeNode("child", "child_content")
            >>> root.add_child(child)
            >>> root.to_dict()
            {'name': 'root', 'content': 'content', 'children': [{'name': 'child', 'content': 'child_content', 'children': []}]}
        """
        return {
            'name': self.name,
            'content': self.content,
            'children': [child.to_dict() for child in self.children]
        }

    def count(self) -> int:
        """
        Count the total number of nodes in the subtree rooted at this node.

        Returns:
            int: The total number of nodes including this node and all descendants

        Example:
            >>> root = TreeNode("root")
            >>> child = TreeNode("child")
            >>> root.add_child(child)
            >>> root.count()
            2
        """
        return 1 + sum(child.count() for child in self.children)

    @staticmethod
    def from_dict(data: Dict) -> 'TreeNode':
        """
        Create a TreeNode from a dictionary representation.
        
        This static method recursively reconstructs a TreeNode and its entire
        subtree from a dictionary structure, typically created by to_dict().
        Parent-child relationships are automatically established.
        
        Args:
            data (Dict): Dictionary containing node data with keys:
                - 'name': The node's name (required)
                - 'content': The node's content (optional)
                - 'children': List of child dictionaries (optional)
                
        Returns:
            TreeNode: The reconstructed node with all children
            
        Example:
            >>> data = {'name': 'root', 'content': 'test', 'children': []}
            >>> node = TreeNode.from_dict(data)
            >>> node.name
            'root'
        """
        node = TreeNode(data['name'], data.get('content'))
        for child_data in data.get('children', []):
            node.add_child(TreeNode.from_dict(child_data))
        return node

    def max_depth(self) -> int:
        """
        Calculate the maximum depth of the subtree rooted at this node.
        
        The depth is defined as the maximum number of nodes from this node
        to any leaf node in its subtree, including this node itself.
        A single node has depth 1.
        
        Returns:
            int: The maximum depth of the subtree
            
        Example:
            >>> root = TreeNode("root")
            >>> child = TreeNode("child")  
            >>> grandchild = TreeNode("grandchild")
            >>> root.add_child(child)
            >>> child.add_child(grandchild)
            >>> root.max_depth()
            3
        """
        if not self.children:
            return 1
        return 1 + max(child.max_depth() for child in self.children)

    def max_width(self) -> int:
        """
        Calculate the maximum width of the subtree rooted at this node.
        
        The width is defined as the maximum number of nodes at any level
        in the subtree. This includes comparing the number of children at
        this level with the maximum width of any child subtree.
        
        Returns:
            int: The maximum width of the subtree
            
        Example:
            >>> root = TreeNode("root")
            >>> child1 = TreeNode("child1")
            >>> child2 = TreeNode("child2")
            >>> child3 = TreeNode("child3")
            >>> root.add_child(child1)
            >>> root.add_child(child2)
            >>> root.add_child(child3)
            >>> root.max_width()
            3
        """
        if not self.children:
            return 1
        widths = [child.max_width() for child in self.children]
        return max(len(self.children), max(widths))

    def summary(self):
        """
        Generate a formatted summary of this node and its subtree.
        
        The summary includes the node's name, content (truncated if long),
        maximum depth, and maximum width of the subtree rooted at this node.
        
        Returns:
            str: A multi-line formatted summary string
            
        Example:
            >>> node = TreeNode("example", "some content")
            >>> child = TreeNode("child", "child content")
            >>> node.add_child(child)
            >>> print(node.summary())
            example: some content
              - Max Depth: 2
              - Max Width: 1
        """
        summary = f"{self.name}:"
        content_str = str(self.content)
        if len(content_str) > 40:
            content_str = content_str[:37] + "..."
        summary += f" {content_str}"
        summary += f"\n  - Max Depth: {self.max_depth()}"
        summary += f"\n  - Max Width: {self.max_width()}"
        summary += f"\n  - Node Count: {self.count()}"
        return summary
    
    def __repr__(self):
        """
        Return a string representation of the TreeNode.
        
        Returns:
            str: A string showing the node's name and number of children
        """
        return f"TreeNode(name={self.name}, children={len(self.children)})"

    def draw(self, key: str = "definition"):
        """
        Print an ASCII art representation of the tree structure.
        
        Args:
            key (str, optional): The dictionary key to display for
                               dictionary content. Defaults to "definition".
        """
        draw_tree(self, key=key)

class Tree:
    """
    A complete tree data structure with a root node and tree operations.
    
    The Tree class provides a high-level interface for working with tree
    structures, including operations for insertion, deletion, modification,
    and serialization. It maintains a reference to the root node and provides
    methods that operate on the entire tree structure.
    
    Attributes:
        root (TreeNode): The root node of the tree
        
    Example:
        >>> root = TreeNode("root", "root content")
        >>> tree = Tree(root)
        >>> child = TreeNode("child", "child content")
        >>> tree.insert("root", child)
        >>> tree.max_depth()
        2
    """
    def __init__(self, root: TreeNode):
        """
        Initialize a new Tree with the given root node.
        
        Args:
            root (TreeNode): The root node of the tree
        """
        self.root = root

    def insert(self, parent_name: str, node: TreeNode):
        """
        Insert a new node as a child of the specified parent node.
        
        This method searches the entire tree for a node with the given
        parent name and adds the new node as its child. If the parent
        is not found, no insertion occurs.
        
        Args:
            parent_name (str): The name of the parent node
            node (TreeNode): The node to insert as a child
            
        Example:
            >>> root = TreeNode("root")
            >>> tree = Tree(root)
            >>> child = TreeNode("child", "content")
            >>> tree.insert("root", child)
            >>> len(root.children)
            1
        """
        parent = self.root.get_subtree(parent_name)
        if parent:
            parent.add_child(node)

    def delete(self, node_name: str):
        """
        Delete a node from the tree by name.
        
        This method finds the node with the specified name and removes it
        from its parent. The root node cannot be deleted (as it has no parent).
        All children of the deleted node are also removed from the tree.
        
        Args:
            node_name (str): The name of the node to delete
            
        Example:
            >>> root = TreeNode("root")
            >>> child = TreeNode("child")
            >>> root.add_child(child)
            >>> tree = Tree(root)
            >>> tree.delete("child")
            >>> len(root.children)
            0
        """
        node = self.root.get_subtree(node_name)
        if node and node.parent:
            node.parent.remove_child(node)

    def alter(self, node_name: str, new_content: Any):
        """
        Modify the content of a node in the tree.
        
        This method finds the node with the specified name and updates
        its content with the new value. If the node is not found,
        no modification occurs.
        
        Args:
            node_name (str): The name of the node to modify
            new_content (Any): The new content to set for the node
            
        Example:
            >>> root = TreeNode("root", "old content")
            >>> tree = Tree(root)
            >>> tree.alter("root", "new content")
            >>> root.content
            'new content'
        """
        node = self.root.get_subtree(node_name)
        if node:
            node.set_content(new_content)

    def get(self, key: Union[str, int]) -> Optional['Tree']:
        """
        Get a subtree by node name or child index.
        
        This method returns a new Tree object rooted at the found node.
        When using a string key, it searches the entire tree. When using
        an integer key, it only looks at direct children of the root.
        
        Args:
            key (Union[str, int]): The identifier for the node. Can be:
                - str: The name of the node (searches entire tree)
                - int: The index of a direct child of root (0-based)
                
        Returns:
            Optional[Tree]: A new Tree rooted at the found node, or None if not found
            
        Example:
            >>> root = TreeNode("root")
            >>> child = TreeNode("child")
            >>> root.add_child(child)
            >>> tree = Tree(root)
            >>> subtree = tree.get("child")
            >>> subtree.root.name
            'child'
        """
        node = None
        if isinstance(key, str):
            node = self.root.get_subtree(key)
        elif isinstance(key, int):
            node = self.root.get_child(key)
        if node:
            return Tree(node)
        return None
    
    def __getitem__(self, key: Union[str, int, slice, list]) -> Optional[Union['Tree', List['Tree']]]:
        """
        Allow access to subtrees using indexing, slicing, or a list of keys.
        For lists, only a list of strings is accepted.

        Args:
            key (Union[str, int, slice, list]): The identifier(s) for the node(s).
        Returns:
            Optional[Tree] or List[Tree]: A subtree or list of subtrees.
        Example:
            >>> tree["child"]      # same as tree.get("child")
            >>> tree[0]            # same as tree.get(0)
            >>> tree[1:3]          # returns list of Tree objects for children 1 and 2
            >>> tree[["child1", "child2"]] # returns list of Tree objects for child1 and child2
        """
        if isinstance(key, int):
            return self.get(key)
        elif isinstance(key, slice):
            indices = range(*key.indices(len(self.root.children)))
            return [self.get(i) for i in indices]
        elif isinstance(key, list):
            if not all(isinstance(k, str) for k in key):
                raise TypeError("List keys must be strings")
            result = []
            for k in key:
                subtree = self.get(k)
                if subtree is not None:
                    result.append(subtree)
            return result
        else:
            return self.get(key)

    def count(self) -> int:
        """
        Count the total number of nodes in the entire tree.
        
        Returns:
            int: The total number of nodes including root and all descendants
        """
        return self.root.count()

    def summary(self):
        """
        Get a formatted summary of the entire tree.
        
        Returns the summary of the root node, which includes information
        about the entire tree structure.
        
        Returns:
            str: A multi-line formatted summary of the tree
            
        Example:
            >>> root = TreeNode("root", "content")
            >>> tree = Tree(root)
            >>> summary = tree.summary()
            >>> "root:" in summary
            True
        """
        return self.root.summary()

    def __repr__(self):
        """
        Return a string representation of the Tree.
        
        Returns:
            str: A string showing the root node, tree depth, and width
        """
        return f"Tree(root={self.root}, depth={self.max_depth()}, width={self.max_width()})"

    def save_json(self, filepath: str):
        """
        Save the tree to a JSON file.
        
        This method serializes the entire tree structure to a JSON file
        using UTF-8 encoding with pretty formatting (2-space indentation).
        
        Args:
            filepath (str): The path where to save the JSON file
            
        Raises:
            IOError: If the file cannot be written
            
        Example:
            >>> root = TreeNode("root", "content")
            >>> tree = Tree(root)
            >>> tree.save_json("my_tree.json")
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.root.to_dict(), f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_json(filepath: str) -> 'Tree':
        """
        Load a tree from a JSON file.
        
        This static method deserializes a tree structure from a JSON file
        and returns a new Tree object. The JSON structure should match
        the format produced by save_json().
        
        Args:
            filepath (str): The path to the JSON file to load
            
        Returns:
            Tree: A new Tree object loaded from the file
            
        Raises:
            IOError: If the file cannot be read
            json.JSONDecodeError: If the file contains invalid JSON
            KeyError: If the JSON structure is invalid
            
        Example:
            >>> tree = Tree.load_json("my_tree.json")
            >>> tree.root.name
            'root'
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        root = TreeNode.from_dict(data)
        return Tree(root)
    
    def max_depth(self) -> int:
        """
        Get the maximum depth of the entire tree.
        
        Returns:
            int: The maximum depth from root to any leaf node
            
        Example:
            >>> root = TreeNode("root")
            >>> child = TreeNode("child")
            >>> root.add_child(child)
            >>> tree = Tree(root)
            >>> tree.max_depth()
            2
        """
        return self.root.max_depth()

    def max_width(self) -> int:
        """
        Get the maximum width of the entire tree.
        
        Returns:
            int: The maximum number of nodes at any level in the tree
            
        Example:
            >>> root = TreeNode("root")
            >>> child1 = TreeNode("child1")
            >>> child2 = TreeNode("child2")
            >>> root.add_child(child1)
            >>> root.add_child(child2)
            >>> tree = Tree(root)
            >>> tree.max_width()
            2
        """
        return self.root.max_width()
    
    def draw(self, key: str = "definition"):
        """
        Print an ASCII art representation of the tree structure.
        
        Args:
            key (str, optional): The dictionary key to display for
                               dictionary content. Defaults to "definition".
        """
        draw_tree(self.root, key=key)

    @staticmethod
    def from_dict(data: Dict):
        """
        Create a Tree from a dictionary representation.
        
        This static method reconstructs a Tree and its entire structure
        from a dictionary, typically created by the to_dict() method.
        
        Args:
            data (Dict): Dictionary containing the tree data
            
        Returns:
            Tree: The reconstructed Tree object
            
        Example:
            >>> data = {'name': 'root', 'content': 'test', 'children': []}
            >>> tree = Tree.from_dict(data)
            >>> tree.root.name
            'root'
        """
        root = TreeNode.from_dict(data)
        return Tree(root)
    
    def to_dict(self) -> Dict:
        """
        Convert the entire tree to a dictionary representation.
        
        This method returns a nested dictionary structure representing
        the entire tree, suitable for JSON serialization.
        
        Returns:
            Dict: A dictionary representation of the tree
        """
        return self.root.to_dict()

def draw_tree(node: TreeNode, prefix: str = "", is_last: bool = True, key: str = "definition"):
    """
    Print an ASCII art representation of a tree structure.
    
    This function recursively prints a tree using Unicode box-drawing
    characters to show the hierarchical structure. It handles special
    formatting for dictionary content with a specified key.
    
    Args:
        node (TreeNode): The root node of the tree/subtree to draw
        prefix (str, optional): The prefix string for indentation. 
                               Used internally for recursion. Defaults to "".
        is_last (bool, optional): Whether this node is the last child
                                of its parent. Used internally for recursion.
                                Defaults to True.
        key (str, optional): The dictionary key to display for dictionary content.
                           If the node's content is a dictionary containing this key,
                           that value will be displayed instead of the entire dictionary.
                           Defaults to "definition".
                                
    Example:
        >>> root = TreeNode("Company", "Acme Corp")
        >>> dept = TreeNode("Engineering", "Tech Department")
        >>> root.add_child(dept)
        >>> draw_tree(root)
        └── Company: Acme Corp
            └── Engineering: Tech Department
            
        >>> # Using custom key
        >>> node = TreeNode("Item", {"desc": "Custom description"})
        >>> draw_tree(node, key="desc")
        └── Item: Custom description
            
    Note:
        If node.content is a dictionary containing the specified key,
        that value will be displayed instead of the entire dictionary.
    """
    connector = "\u2514\u2500\u2500 " if is_last else "\u251c\u2500\u2500 "
    content_display = node.content
    if isinstance(node.content, dict) and key in node.content:
        content_display = node.content[key]
    
    print(prefix + connector + f"{node.name}: {content_display}")
    new_prefix = prefix + ("    " if is_last else "│   ")
    for i, child in enumerate(node.children):
        draw_tree(child, new_prefix, i == len(node.children) - 1, key)