"""A set of XML adapters for the datastore module."""

from .deserialize import XMLDeserializer
from .serialize import XMLSeralizer

__all__ = ["XMLDeserializer", "XMLSeralizer"]
