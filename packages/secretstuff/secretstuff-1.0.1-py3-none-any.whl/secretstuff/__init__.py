"""
SecretStuff - A comprehensive PII redaction and reverse mapping library.

This package provides tools for identifying, redacting, and reversing personally 
identifiable information (PII) in text documents using advanced NLP models.
"""

from .core.identifier import PIIIdentifier
from .core.redactor import PIIRedactor
from .core.reverse_mapper import ReverseMapper
from .api.pipeline import SecretStuffPipeline
from .config.labels import DEFAULT_LABELS
from .config.dummy_values import DEFAULT_DUMMY_VALUES

__version__ = "1.0.1"
__author__ = "axondendrite", "Aksman"
__email__ = "amandogra2016@gmail.com", "akshatmanihar580@gmail.com"

__all__ = [
    "PIIIdentifier",
    "PIIRedactor", 
    "ReverseMapper",
    "SecretStuffPipeline",
    "DEFAULT_LABELS",
    "DEFAULT_DUMMY_VALUES"
]
