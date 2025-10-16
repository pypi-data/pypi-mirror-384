"""
Feature creation Agent Package

An intelligent agent for creating new features for machine learning tasks.
"""

from .agent import FeatureSuggestionAgent
from .models import (
    FeatureInput, 
    FeatureOutput, 
    FeaturesListModel
)

__version__ = "1.0.0"
__all__ = [
    "FeatureSuggestionAgent",
    "FeatureInput",
    "FeatureOutput",
    "FeaturesListModel"
]