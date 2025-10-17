from __future__ import annotations
from abc import ABC, abstractmethod


class Spatial(ABC):
    """Common interface for all 2D geometric objects that can undergo spatial transforms.
    All transformations mutate in place.
    """

    # --------------------------------------------------------
    # Abstract transformation API
    # --------------------------------------------------------
    @abstractmethod
    def translate(self, dx: float, dy: float) -> "Spatial":
        """Translate by (dx, dy)."""
        ...

    @abstractmethod
    def rotate(self, angle_deg: float, center: tuple[float, float] | None = None) -> "Spatial":
        """Rotate around a given center."""
        ...

    @abstractmethod
    def resize(self, scale_x: float, scale_y: float, center: tuple[float, float] | None = None) -> "Spatial":
        """Scale relative to a given center."""
        ...

    @abstractmethod
    def mirror(self, point: tuple[float, float] = (0, 0), angle: float = 0.0) -> "Spatial":
        """Mirror across a line passing through `point` at `angle` degrees."""
        ...

    # --------------------------------------------------------
    # Common helpers
    # --------------------------------------------------------
    def scale(self, factor: float, center: tuple[float, float] | None = None) -> "Spatial":
        """Uniform scaling."""
        return self.resize(factor, factor, center)

    def mirror_vertical(self, x: float = 0.0) -> "Spatial":
        """Mirror across a vertical axis (angle = 90°)."""
        return self.mirror(point=(x, 0), angle=90.0)

    def mirror_horizontal(self, y: float = 0.0) -> "Spatial":
        """Mirror across a horizontal axis (angle = 0°)."""
        return self.mirror(point=(0, y), angle=0.0)
