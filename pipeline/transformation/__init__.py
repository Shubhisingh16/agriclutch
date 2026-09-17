"""
AgriClutch Data Transformation Pipeline Package.
Transforms cleaned records into model-ready time-series features and lead-lag representations.
"""

from pipeline.transformation.base import BaseTransformer

__all__ = ["BaseTransformer"]
