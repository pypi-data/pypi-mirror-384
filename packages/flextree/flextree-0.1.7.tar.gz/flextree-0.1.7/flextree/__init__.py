"""
FlexTree - A flexible and intuitive Python library for creating and manipulating tree data structures.

This package provides TreeNode and Tree classes for building hierarchical data structures,
along with utilities for visualization, serialization, and manipulation.
"""

from .flextree import TreeNode, Tree, draw_tree
from .examples import examples

__version__ = "0.1.6"
__author__ = "Zhenning Zhao"
__email__ = "znzhaopersonal@gmail.com"

__all__ = ["TreeNode", "Tree", "draw_tree", "examples"]