"""This module provides utilities for handling corrective factors for RGB values,"""

from typing import Literal

from pydantic import BaseModel, Field, computed_field

from bear_dereth.math.general import relative_norm as norm

MAX_RGB = 255.0


class RGBValues(BaseModel):
    """Pydantic model for RGB values and their corrective factors."""

    r_: int = Field(..., description="Integer value for red channel", exclude=True)
    g_: int = Field(..., description="Integer value for green channel", exclude=True)
    b_: int = Field(..., description="Integer value for blue channel", exclude=True)

    @property
    def r(self) -> int:
        """Return the red channel value."""
        return self.r_

    @r.setter
    def r(self, value: int) -> None:
        """Set the red channel value."""
        if not (0 <= value <= MAX_RGB):
            raise ValueError("Red value must be between 0 and 255.")
        self.r_ = value

    @property
    def g(self) -> int:
        """Return the green channel value."""
        return self.g_

    @g.setter
    def g(self, value: int) -> None:
        """Set the green channel value."""
        if not (0 <= value <= MAX_RGB):
            raise ValueError("Green value must be between 0 and 255.")
        self.g_ = value

    @property
    def b(self) -> int:
        """Return the blue channel value."""
        return self.b_

    @b.setter
    def b(self, value: int) -> None:
        """Set the blue channel value."""
        if not (0 <= value <= MAX_RGB):
            raise ValueError("Blue value must be between 0 and 255.")
        self.b_ = value

    @property
    def normalized_red(self) -> float:
        """Return the normalized red channel correction factor."""
        return norm(self.r, MAX_RGB)

    @property
    def normalized_green(self) -> float:
        """Green is always the reference channel, so it is always 1.0."""
        return 1.0

    @property
    def normalized_blue(self) -> float:
        """Return the normalized blue channel correction factor."""
        return norm(self.b, MAX_RGB)

    @property
    def factor_red(self) -> float:
        """Return the red channel correction factor."""
        if self.normalized_red <= 0:
            raise ValueError("Normalized red value cannot be zero or negative.")
        return self.normalized_green / self.normalized_red

    @property
    def factor_green(self) -> float:
        """Always returns 1.0 as green is the reference channel."""
        return self.normalized_green

    @property
    def factor_blue(self) -> float:
        """Return the blue channel correction factor."""
        if self.normalized_blue <= 0:
            raise ValueError("Normalized blue value cannot be zero or negative.")
        return self.normalized_green / self.normalized_blue

    @computed_field
    @property
    def red(self) -> str:
        """Return the red channel correction factor as a string."""
        return str(self.factor_red)

    @computed_field
    @property
    def green(self) -> Literal["1.0"]:
        """Return the green channel correction factor as a string."""
        return "1.0"

    @computed_field
    @property
    def blue(self) -> str:
        """Return the blue channel correction factor as a string."""
        return str(self.factor_blue)

    def to_string(self, raw: bool = False) -> str:
        """Return a string representation of the raw RGB values."""
        if raw:
            return f"RawRGB(r={self.r}, g={self.g}, b={self.b})"
        return f"CorrectiveFactors(r={self.red}, g={self.green}, b={self.blue})"


__all__ = ["RGBValues"]
