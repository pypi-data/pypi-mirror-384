#!/usr/bin/env python3
"""
FlexTree Examples

A concise demonstration of the most important features of the flextree module.

Run: python examples.py
"""

import os
from flextree import TreeNode, Tree, draw_tree

def quick_start_example():
    """Quick start guide - most common operations."""
    print("FlexTree Quick Start Guide")
    print("=" * 40)
    
    # 1. Create a simple tree
    print("1. Creating a simple tree:")
    print("CODE:")
    print('   from flextree import TreeNode, Tree, draw_tree')
    print()
    print('   root = TreeNode("Company", "Acme Corp")')
    print('   engineering = TreeNode("Engineering", "Tech Team")')
    print('   marketing = TreeNode("Marketing", "Growth Team")')
    print()
    print('   root.add_child(engineering)')
    print('   root.add_child(marketing)')
    print()
    print('   # Add sub-teams')
    print('   backend = TreeNode("Backend", "Server Development")')
    print('   frontend = TreeNode("Frontend", "UI Development")')
    print('   engineering.add_child(backend)')
    print('   engineering.add_child(frontend)')
    print()
    print('   draw_tree(root)')
    print()
    
    root = TreeNode("Company", "Acme Corp")
    engineering = TreeNode("Engineering", "Tech Team")
    marketing = TreeNode("Marketing", "Growth Team")
    
    root.add_child(engineering)
    root.add_child(marketing)
    
    # Add sub-teams
    backend = TreeNode("Backend", "Server Development")
    frontend = TreeNode("Frontend", "UI Development")
    engineering.add_child(backend)
    engineering.add_child(frontend)
    
    print("OUTPUT:")
    draw_tree(root)
    
    # 2. Use Tree class for operations
    print("\n2. Using Tree class for operations:")
    print("CODE:")
    print('   company_tree = Tree(root)')
    print('   hr = TreeNode("HR", "Human Resources")')
    print('   company_tree.insert("Company", hr)')
    print('   company_tree.alter("Backend", "Backend & DevOps")')
    print('   company_tree.delete("Frontend")')
    print()
    company_tree = Tree(root)
    
    # Add new department
    hr = TreeNode("HR", "Human Resources")
    company_tree.insert("Company", hr)
    
    # Modify existing content
    company_tree.alter("Backend", "Backend & DevOps")
    
    print("Updated tree:")
    draw_tree(company_tree.root)

    company_tree.delete("Frontend")
    print("Tree after deleting 'Frontend':")
    draw_tree(company_tree.root)

    # 3. Get statistics
    print(f"\n3. Tree statistics:")
    print("CODE:")
    print('   print(f"Node count: {company_tree.count()} nodes")')
    print('   print(f"Depth: {company_tree.max_depth()} levels")')
    print('   print(f"Width: {company_tree.max_width()} max nodes at one level")')
    print()
    print("Output:")
    print(f"   Node count: {company_tree.count()} nodes")
    print(f"   Depth: {company_tree.max_depth()} levels")
    print(f"   Width: {company_tree.max_width()} max nodes at one level")
    print()

    # 4. Search operations
    print(f"\n4. Finding nodes:")
    print("CODE:")
    print('   eng_dept = company_tree.get("Engineering")')
    print('   if eng_dept:')
    print('       print(f"Found Engineering department with {len(eng_dept.root.children)} teams")')
    print('       draw_tree(eng_dept.root)')
    print()
    print("Output:")
    eng_dept = company_tree.get("Engineering")
    if eng_dept:
        print(f"Found Engineering department with {len(eng_dept.root.children)} teams")
        draw_tree(eng_dept.root)
    
    # 5. JSON serialization
    print(f"\n5. JSON serialization:")
    temp_file = "temp_tree.json"
    print("CODE:")
    print('   temp_file = "temp_tree.json"  # or use tempfile for a temp file')
    print('   company_tree.save_json(temp_file)')
    print('   loaded_tree = Tree.load_json(temp_file)')
    print()
    print("Output:")
    try:
        company_tree.save_json(temp_file)
        loaded_tree = Tree.load_json(temp_file)
        print(f"   Saved and loaded successfully!")
        print(f"   Loaded tree has {len(loaded_tree.root.children)} top-level departments")
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def getitem_indexing_example():
    """Show how to use getitem operations for easy tree navigation."""
    print("\n" + "=" * 40)
    print("GetItem Indexing Example")
    print("=" * 40)
    
    # Create a sample tree
    print("1. Creating a simple team structure:")
    print("CODE:")
    print('   team = TreeNode("Team", "Development Team")')
    print('   alice = TreeNode("Alice", "Team Lead")')
    print('   bob = TreeNode("Bob", "Developer")')
    print('   charlie = TreeNode("Charlie", "Designer")')
    print()
    print('   team.add_child(alice)')
    print('   team.add_child(bob)')
    print('   team.add_child(charlie)')
    print()
    
    team = TreeNode("Team", "Development Team")
    alice = TreeNode("Alice", "Team Lead")
    bob = TreeNode("Bob", "Developer") 
    charlie = TreeNode("Charlie", "Designer")
    
    team.add_child(alice)
    team.add_child(bob)
    team.add_child(charlie)
    
    print("OUTPUT:")
    draw_tree(team)
    
    print("\n2. Create Tree object for getitem operations:")
    print("CODE:")
    print('   # TreeNode objects do not support getitem - need Tree object')
    print('   dev_team = Tree(team)')
    print('   # Access by name (dictionary-style) - returns Tree object')
    print('   alice_tree = dev_team["Alice"]')
    print('   print(f"Found by name: {alice_tree.root.name if alice_tree else None}")')
    print()
    print('   # Access by index (list-style) - returns Tree object')
    print('   first_tree = dev_team[0]')
    print('   print(f"First member: {first_tree.root.name if first_tree else None}")')
    print()
    print('   # Get multiple members with slicing - returns list of Tree objects')
    print('   last_two_trees = dev_team[1:]')
    print('   print(f"Last two: {[tree.root.name for tree in last_two_trees]}")')
    print()
    
    # Create Tree object first
    dev_team = Tree(team)
    
    # Access by name (dictionary-style)
    alice_tree = dev_team["Alice"]
    print(f"Output: Found by name: {alice_tree.root.name if alice_tree else None}")
    
    # Access by index (list-style)
    first_tree = dev_team[0]
    print(f"Output: First member: {first_tree.root.name if first_tree else None}")
    
    # Get multiple with slicing
    last_two_trees = dev_team[1:]
    print(f"Output: Last two: {[tree.root.name for tree in last_two_trees]}")
    
    print("\n3. Advanced getitem features:")
    print("CODE:")
    print('   # Get multiple specific members by name list (strings only)')
    print('   selected_trees = dev_team[["Alice", "Charlie"]]')
    print('   print(f"Selected: {[tree.root.name for tree in selected_trees]}")')
    print()
    print('   # Chain operations for nested access')
    print('   intern = TreeNode("Intern", "Junior Developer")')
    print('   dev_team.insert("Alice", intern)')
    print('   alice_subtree = dev_team["Alice"]')
    print('   if alice_subtree:')
    print('       alice_team = alice_subtree[:]  # Get all under Alice')
    print('       print(f"Alice\'s team: {[t.root.name for t in alice_team]}")')
    print()
    
    # Get multiple specific members by name list
    selected_trees = dev_team[["Alice", "Charlie"]]
    print(f"Output: Selected: {[tree.root.name for tree in selected_trees]}")
    
    # Chain operations for nested access
    intern = TreeNode("Intern", "Junior Developer")
    dev_team.insert("Alice", intern)
    alice_subtree = dev_team["Alice"]
    if alice_subtree:
        alice_team = alice_subtree[:]  # Get all under Alice
        print(f"Output: Alice's team: {[t.root.name for t in alice_team]}")
    
    print("\n4. Key benefits of Tree getitem:")
    print("   - Only Tree objects support getitem (not TreeNode)")
    print("   - tree['name'] returns Tree objects for easy chaining") 
    print("   - Supports [index] and [start:end] slicing")
    print("   - List keys must be strings only: tree[['name1', 'name2']]")
    print("   - Makes tree navigation feel like native Python!")

class Examples():
    def __init__(self):
        pass
    def run(self):
        """Run all quick examples."""
        print("flextree - Quick Examples\n")
        print("=" * 40)
        print("READY-TO-COPY CODE EXAMPLES")
        print("=" * 40)
        print("These examples show the most important features of flextree.")
        print("Each example includes CODE you can copy and paste directly!\n")
        print("=" * 40)
        
        quick_start_example()
        getitem_indexing_example()
        
        print("\n" + "=" * 40)
        print("Quick Examples Complete!")
        print("=" * 40)
        print("HOW TO USE:")
        print("1. Copy any CODE section from the examples above")
        print("2. Paste into your Python environment")
        print("3. Run to see the same OUTPUT")

examples = Examples()

if __name__ == "__main__":
    examples.run()