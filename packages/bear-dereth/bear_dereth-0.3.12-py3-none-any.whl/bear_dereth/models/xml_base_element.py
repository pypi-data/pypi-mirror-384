"""A base class for XML elements using Pydantic models."""

from __future__ import annotations

from typing import Any, ClassVar, Literal, Self, overload
from xml.etree.ElementTree import Element, tostring

from pydantic import BaseModel, Field, SerializerFunctionWrapHandler, model_serializer

from bear_dereth.files.xml.helpers import to_elem


class AbstractElement:
    """Abstract base class for XML elements with a tag attribute."""

    tag: ClassVar[str]

    def to_xml(self) -> Element:
        """Convert the model attributes to an XML element.

        Returns:
            An XML Element representing the model.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class BaseElement[T: AbstractElement](BaseModel, AbstractElement):
    """Base model for XML elements with a tag attribute."""

    model_config = {"arbitrary_types_allowed": True}

    tag: ClassVar[str] = ""
    sub_elements: list[T] = Field(default_factory=list, description="Sub-elements of other XML elements.")

    @model_serializer(mode="wrap")
    def convert_to_strings(self, nxt: SerializerFunctionWrapHandler) -> dict[Any, Any]:
        """Convert common types to strings for XML serialization."""
        data: dict[Any, Any] = nxt(self)

        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, (int | float | bool)):
                data[key] = str(value).lower()
        return data

    def add(self, element: T) -> Self:
        """Add a sub-element to the list of sub-elements."""
        if not isinstance(element, BaseElement):
            raise TypeError(f"Expected an instance of BaseElement, got {type(element)}")
        self.sub_elements.append(element)
        return self

    def has_element(self, element: type[T] | str) -> bool:
        """Check if the element is present in the sub-elements."""
        if isinstance(element, str):
            return any(sub.tag == element for sub in self.sub_elements)
        if isinstance(element, type) and issubclass(element, BaseElement):
            return any(isinstance(sub, element) for sub in self.sub_elements)
        return element in self.sub_elements

    def has_field(self, attr: type | str) -> bool:
        """Check if the class has a specific field or attribute."""
        if isinstance(attr, str):
            return hasattr(self, attr)
        return hasattr(self, attr.__name__)

    @overload
    def get(self, element: str, required: Literal[True]) -> T: ...

    @overload
    def get(self, element: type[T], required: Literal[True]) -> T: ...

    @overload
    def get(self, element: type[T], required: Literal[False] = False) -> T | None: ...

    @overload
    def get(self, element: str, required: Literal[False] = False) -> T | None: ...

    def get(self, element: type[T] | str, required: bool = False) -> T | None:
        """Get the sub-element by element type or tag name."""
        if isinstance(element, type):
            for sub in self.sub_elements:
                if isinstance(sub, element):
                    return sub
        elif isinstance(element, str):
            for sub in self.sub_elements:
                if sub.tag == element:
                    return sub
        if required:
            raise ValueError(f"Element '{element}' not found in sub_elements")
        return None

    def get_req(self, element: T | str) -> T:
        """Get the sub-element by element type or tag name, raising an error if not found."""
        return self.get(element, required=True)

    def to_xml(self, exclude_none: bool = True, exclude: set | None = None, **kwargs) -> Element:
        """Convert the model attributes to an XML element.

        Returns:
            An XML Element representing the model.
        """
        if exclude is None:
            exclude_me: set[str] = {"sub_elements"}
        else:
            exclude_me: set[str] = exclude.union({"sub_elements"})
        element: Element = to_elem(
            tag=self.tag,
            **self.model_dump(
                exclude_none=exclude_none,
                exclude=exclude_me,
                **kwargs,
            ),
        )
        if self.sub_elements:
            for sub_element in self.sub_elements:
                sub_element_element: Element = sub_element.to_xml()
                element.append(sub_element_element)
        return element

    def to_string(self) -> str:
        """Convert the model to a string representation."""
        return tostring(self.to_xml(), encoding="unicode")
