"""
Synthesis module - DEPRECATED

This module has been replaced by rebrain.operations.

New imports:
    from rebrain.operations import GenericSynthesizer, Embedder, Clusterer, PrivacyFilter

Old classes archived as .bak files for reference.
"""

# For backward compatibility, redirect to new modules
from rebrain.operations.synthesizer import GenericSynthesizer
from rebrain.operations.embedder import Embedder
from rebrain.operations.clusterer import Clusterer
from rebrain.operations.filter import PrivacyFilter

__all__ = [
    "GenericSynthesizer",
    "Embedder", 
    "Clusterer",
    "PrivacyFilter",
]