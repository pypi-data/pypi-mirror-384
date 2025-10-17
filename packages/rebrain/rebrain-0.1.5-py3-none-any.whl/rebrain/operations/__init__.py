"""
Consolidated operations module for rebrain pipeline.

All core operations: embedding, clustering, synthesis, filtering.
"""

from rebrain.operations.embedder import Embedder
from rebrain.operations.clusterer import Clusterer
from rebrain.operations.synthesizer import GenericSynthesizer
from rebrain.operations.filter import DateFilter, PrivacyFilter

__all__ = [
    "Embedder",
    "Clusterer",
    "GenericSynthesizer",
    "DateFilter",
    "PrivacyFilter",
]

