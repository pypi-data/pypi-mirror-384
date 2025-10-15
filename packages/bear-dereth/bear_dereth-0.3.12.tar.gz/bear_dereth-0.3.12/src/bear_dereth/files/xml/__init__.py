"""A set of helpers for XML file handling."""

from typing import TYPE_CHECKING
from xml.etree.ElementTree import Element, ElementTree

if TYPE_CHECKING:
    Tree = ElementTree[Element]
else:
    Tree = ElementTree

from bear_dereth.files.xml.file_handler import XMLFilehandler
from bear_dereth.files.xml.helpers import to_elem
from bear_dereth.models.xml_base_element import AbstractElement, BaseElement

__all__ = [
    "AbstractElement",
    "BaseElement",
    "Element",
    "ElementTree",
    "Tree",
    "XMLFilehandler",
    "to_elem",
]
