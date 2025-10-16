"""
BEDCA (Spanish Food Composition Database) API client.

This package provides a Python interface to interact with the BEDCA database.
"""

from .client import BedcaClient
from .models import FoodPreview, Food

__all__ = ["BedcaClient", "FoodPreview", "Food"]
