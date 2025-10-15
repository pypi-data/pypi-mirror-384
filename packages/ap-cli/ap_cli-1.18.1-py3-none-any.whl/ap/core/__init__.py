"""
Core module for the ap learning tool.

This module contains the core data structures and functionality
for managing multi-topic concept maps.
"""

from .concept_map import ConceptMap, slugify

__all__ = ['ConceptMap', 'slugify']