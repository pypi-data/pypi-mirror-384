"""A color gradient utility for generating RGB colors based on thresholds."""

from pydantic import BaseModel
from rich.color import Color as RichColor
from rich.color_triplet import ColorTriplet

from bear_dereth.math.general import inv_lerp, lerp

RED: RichColor = RichColor.from_rgb(255, 0, 0)
YELLOW: RichColor = RichColor.from_rgb(255, 255, 0)
GREEN: RichColor = RichColor.from_rgb(0, 255, 0)


def clamp(v: float, low: float, high: float) -> float:
    """Clamp a value between a minimum and maximum."""
    return max(low, min(v, high))


def rgb_int(v: float) -> int:
    """Convert a float to an int, clamping to 0-255."""
    return int(clamp(v, 0.0, 255.0))


class DefaultColors(BaseModel):
    """The default colors for the gradient."""

    model_config = {"arbitrary_types_allowed": True}

    start: RichColor = RED  # Default Threshold: 0.0
    mid: RichColor = YELLOW  # Default Threshold: 0.7
    end: RichColor = GREEN  # Default Threshold: 1.0

    def output_rgb(self) -> tuple[ColorTriplet, ColorTriplet, ColorTriplet]:
        """Get the RGB values of the default colors."""
        return self.start.get_truecolor(), self.mid.get_truecolor(), self.end.get_truecolor()


class DefaultThresholds(BaseModel):
    """The default thresholds for the gradient."""

    start: float = 0.0  # Default Color: RED
    mid: float = 0.7  # Default Color: YELLOW
    end: float = 1.0  # Default Color: GREEN

    def __post_init__(self) -> None:
        if not (0.0 <= self.start < self.mid < self.end <= 1.0):
            raise ValueError("thresholds must be strictly increasing and between 0 and 1.")

    def unpack(self) -> tuple[float, float, float]:
        """Unpack the thresholds into a tuple."""
        return self.start, self.mid, self.end


class DefaultColorConfig:
    """Configuration for the default color gradient."""

    colors: DefaultColors = DefaultColors()
    thresholds: DefaultThresholds = DefaultThresholds()


class ColorGradient:
    """Simple 3-color gradient interpolator.

    Args:
        colors (DefaultColors): Default colors for the gradient.
        thresholds (Thresholds): Thresholds for the gradient.
        reverse (bool): If True, reverses the gradient direction.
    """

    def __init__(self, config: DefaultColorConfig | None = None, reverse: bool = False) -> None:
        """Initialize the ColorGradient with a configuration and optional reverse flag."""
        self.config: DefaultColorConfig = config or DefaultColorConfig()
        self.colors: DefaultColors = self.config.colors
        self.thresholds: DefaultThresholds = self.config.thresholds
        self.reverse: bool = reverse
        self.c0, self.c1, self.c2 = self.colors.output_rgb()
        self.p0, self.p1, self.p2 = self.thresholds.unpack()

        if not (0.0 <= self.p0 < self.p1 < self.p2 <= 1.0):
            raise ValueError("thresholds must be strictly increasing and between 0 and 1.")

    def flip(self) -> None:
        """Toggle the reverse flag."""
        self.reverse = not self.reverse

    def map_to_rgb(self, _min: float, _max: float, v: float, reverse: bool | None = None) -> str:
        """Get rgb color for a value by linear interpolation.

        Args:
            _min (float): Minimum of input range.
            _max (float): Maximum of input range.
            v (float): Value to map.
            reverse (bool | None): If True, reverses the gradient direction.

        Returns:
            str: RGB color string.
        """
        return self.map_to_color(_min, _max, v, reverse).rgb

    def map_to_color(self, _min: float, _max: float, v: float, reverse: bool | None = None) -> ColorTriplet:
        """Get rgb color for a value by linear interpolation.

        Args:
            _min (float): Minimum of input range.
            _max (float): Maximum of input range.
            v (float): Value to map.

        Returns:
            ColorTriplet: RGB color triplet.
        """
        reverse = reverse if reverse is not None else self.reverse

        t: float = inv_lerp(_min, _max, v) if not reverse else 1.0 - inv_lerp(_min, _max, v)
        src, dst = (self.c0, self.c1) if t <= self.p1 else (self.c1, self.c2)
        seg: float = inv_lerp(self.p0, self.p1, t) if t <= self.p1 else inv_lerp(self.p1, self.p2, t)

        r: int = rgb_int(lerp(src.red, dst.red, seg))
        g: int = rgb_int(lerp(src.green, dst.green, seg))
        b: int = rgb_int(lerp(src.blue, dst.blue, seg))

        return ColorTriplet(red=r, green=g, blue=b)
