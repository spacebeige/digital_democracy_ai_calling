"""
Output Management Module
========================
Handles organizing and storing grievance analysis results
in logical folder structures for easy querying and analytics.
"""

from .json_storage_manager import JSONStorageManager
from .organize_results import OrganizeResultsHelper

__all__ = ['JSONStorageManager', 'OrganizeResultsHelper']
