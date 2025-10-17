from __future__ import annotations
from dataclasses import dataclass
from typing import TypeAlias, Tuple
from math import sin, cos, radians
from .spatial import Spatial

# ------------------------------------------------------------
# Type alias
# ------------------------------------------------------------
PointLike: TypeAlias = "Point | Tuple[float, float]"


@dataclass
class Point(Spatial):
    """A simple 2D point supporting direct affine transformations.
    All transformations mutate the point in place.
    """

    x: float = 0.0
    y: float = 0.0

    # --------------------------------------------------------
    # Construction and conversion
    # --------------------------------------------------------
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)

    # --------------------------------------------------------
    # Spatial transformations (in place)
    # --------------------------------------------------------
    def translate(self, dx: float, dy: float) -> "Point":
        """Translate by (dx, dy)."""
        self.x += dx
        self.y += dy
        return self

    def rotate(self, angle_deg: float, center: PointLike | None = None) -> "Point":
        """Rotate around a given center (defaults to origin)."""
        if center is None:
            cx, cy = 0.0, 0.0
        else:
            cx, cy = to_point(center).as_tuple()

        dx = self.x - cx
        dy = self.y - cy
        a = radians(angle_deg)

        self.x = cx + dx * cos(a) - dy * sin(a)
        self.y = cy + dx * sin(a) + dy * cos(a)
        return self

    def resize(self, scale_x: float, scale_y: float, center: PointLike | None = None) -> "Point":
        """Scale relative to a given center (defaults to origin)."""
        if center is None:
            cx, cy = 0.0, 0.0
        else:
            cx, cy = to_point(center).as_tuple()

        self.x = cx + (self.x - cx) * scale_x
        self.y = cy + (self.y - cy) * scale_y
        return self

    def mirror(self, point: PointLike = (0, 0), angle: float = 0.0) -> "Point":
        """Mirror across a line passing through `point` at `angle` degrees."""
        px, py = to_point(point).as_tuple()
        a = radians(angle)

        dx = self.x - px
        dy = self.y - py

        # rotate so the mirror line aligns with x-axis
        dx_rot = dx * cos(a) + dy * sin(a)
        dy_rot = -dx * sin(a) + dy * cos(a)

        # reflect across x-axis (invert y)
        dy_rot = -dy_rot

        # rotate back
        self.x = px + dx_rot * cos(a) - dy_rot * sin(a)
        self.y = py + dx_rot * sin(a) + dy_rot * cos(a)
        return self

    # --------------------------------------------------------
    # Utility
    # --------------------------------------------------------
    def __iter__(self):
        yield self.x
        yield self.y

    def __repr__(self) -> str:
        return f"Point({self.x:.2f}, {self.y:.2f})"


def to_point(p: Tuple[float, float] | Point) -> Point:
    if isinstance(p, Point):
        return p
    else:
        return Point(p[0], p[1])
