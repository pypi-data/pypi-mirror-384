from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Self
from abc import ABC, abstractmethod
import copy

from .point import Point, PointLike, to_point
from .style import Style


# ----------------------------------------------------------------------
# Abstract Base Primitive
# ----------------------------------------------------------------------

@dataclass(kw_only=True)
class Primitive(ABC):
    style: Style = field(default_factory=Style)

    # ------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------
    @abstractmethod
    def center(self) -> Point:
        ...

    @abstractmethod
    def translate(self, dx: float, dy: float) -> Self:
        ...

    @abstractmethod
    def rotate(self, angle_deg: float, center: PointLike | None = None) -> Self:
        ...

    @abstractmethod
    def resize(self, scale_x: float, scale_y: float, center: PointLike | None = None) -> Self:
        ...

    @abstractmethod
    def mirror(self, point: PointLike = (0, 0), angle: float = 0.0) -> Self:
        ...

    # ------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------
    def copy(self) -> Self:
        """Return a deep copy of this primitive."""
        return copy.deepcopy(self)

    def set_style(self, style: Style) -> Self:
        self.style = style
        return self

    def scale(self, factor: float, center: PointLike | None = None) -> Self:
        return self.resize(factor, factor, center)

    def mirror_vertical(self, x: float = 0.0) -> Self:
        return self.mirror(point=(x, 0), angle=90.0)

    def mirror_horizontal(self, y: float = 0.0) -> Self:
        return self.mirror(point=(0, y), angle=0.0)


# ----------------------------------------------------------------------
# Line
# ----------------------------------------------------------------------

@dataclass
class Line(Primitive):
    start: Point
    end: Point

    def __init__(self, start: PointLike = (0, 0), end: PointLike = (0, 0), **kwargs):
        super().__init__(**kwargs)
        self.start = to_point(start)
        self.end = to_point(end)

    def center(self) -> Point:
        return Point((self.start.x + self.end.x) / 2, (self.start.y + self.end.y) / 2)

    def translate(self, dx: float, dy: float) -> Self:
        self.start.translate(dx, dy)
        self.end.translate(dx, dy)
        return self

    def rotate(self, angle_deg: float, center: PointLike | None = None) -> Self:
        c = to_point(center or self.center())
        self.start.rotate(angle_deg, c)
        self.end.rotate(angle_deg, c)
        return self

    def resize(self, scale_x: float, scale_y: float, center: PointLike | None = None) -> Self:
        c = to_point(center or self.center())
        self.start.resize(scale_x, scale_y, c)
        self.end.resize(scale_x, scale_y, c)
        return self

    def mirror(self, point: PointLike = (0, 0), angle: float = 0.0) -> Self:
        self.start.mirror(point, angle)
        self.end.mirror(point, angle)
        return self


# ----------------------------------------------------------------------
# Circle
# ----------------------------------------------------------------------

@dataclass
class Circle(Primitive):
    center_point: Point
    radius: float = 1.0

    def __init__(self, center: PointLike = (0, 0), radius: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.center_point = to_point(center)
        self.radius = radius

    def center(self) -> Point:
        return self.center_point

    def translate(self, dx: float, dy: float) -> Self:
        self.center_point.translate(dx, dy)
        return self

    def rotate(self, angle_deg: float, center: PointLike | None = None) -> Self:
        c = to_point(center or self.center_point)
        self.center_point.rotate(angle_deg, c)
        return self

    def resize(self, scale_x: float, scale_y: float, center: PointLike | None = None) -> Self:
        c = to_point(center or self.center_point)
        self.center_point.resize(scale_x, scale_y, c)
        self.radius *= (scale_x + scale_y) / 2
        return self

    def mirror(self, point: PointLike = (0, 0), angle: float = 0.0) -> Self:
        self.center_point.mirror(point, angle)
        return self


# ----------------------------------------------------------------------
# Rectangle
# ----------------------------------------------------------------------

@dataclass
class Rectangle(Primitive):
    pos: Point
    size: tuple[float, float] = (1, 1)

    def __init__(self, pos: PointLike = (0, 0), size: tuple[float, float] = (1, 1), **kwargs):
        super().__init__(**kwargs)
        self.pos = to_point(pos)
        self.size = size

    def center(self) -> Point:
        w, h = self.size
        x, y = self.pos.as_tuple()
        return Point(x + w / 2, y + h / 2)

    def translate(self, dx: float, dy: float) -> Self:
        self.pos.translate(dx, dy)
        return self

    def rotate(self, angle_deg: float, center: PointLike | None = None) -> Self:
        c = to_point(center or self.center())
        self.pos.rotate(angle_deg, c)
        return self

    def resize(self, scale_x: float, scale_y: float, center: PointLike | None = None) -> Self:
        c = to_point(center or self.center())
        self.pos.resize(scale_x, scale_y, c)
        self.size = (self.size[0] * scale_x, self.size[1] * scale_y)
        return self

    def mirror(self, point: PointLike = (0, 0), angle: float = 0.0) -> Self:
        self.pos.mirror(point, angle)
        return self


# ----------------------------------------------------------------------
# Polyline
# ----------------------------------------------------------------------

@dataclass
class Polyline(Primitive):
    points: List[Point] = field(default_factory=list)

    def __init__(self, points: List[PointLike] | None = None, **kwargs):
        super().__init__(**kwargs)
        self.points = [to_point(p) for p in (points or [])]

    def center(self) -> Point:
        if not self.points:
            return Point(0, 0)
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        return Point(sum(xs) / len(xs), sum(ys) / len(ys))

    def translate(self, dx: float, dy: float) -> Self:
        for p in self.points:
            p.translate(dx, dy)
        return self

    def rotate(self, angle_deg: float, center: PointLike | None = None) -> Self:
        c = to_point(center or self.center())
        for p in self.points:
            p.rotate(angle_deg, c)
        return self

    def resize(self, scale_x: float, scale_y: float, center: PointLike | None = None) -> Self:
        c = to_point(center or self.center())
        for p in self.points:
            p.resize(scale_x, scale_y, c)
        return self

    def mirror(self, point: PointLike = (0, 0), angle: float = 0.0) -> Self:
        for p in self.points:
            p.mirror(point, angle)
        return self


# ----------------------------------------------------------------------
# Arc
# ----------------------------------------------------------------------

@dataclass
class Arc(Primitive):
    center_point: Point
    radius: float = 1.0
    start_angle: float = 0.0
    end_angle: float = 90.0

    def __init__(self, center: PointLike = (0, 0), radius: float = 1.0, start_angle: float = 0.0, end_angle: float = 90.0, **kwargs):
        super().__init__(**kwargs)
        self.center_point = to_point(center)
        self.radius = radius
        self.start_angle = start_angle
        self.end_angle = end_angle

    def center(self) -> Point:
        return self.center_point

    def translate(self, dx: float, dy: float) -> Self:
        self.center_point.translate(dx, dy)
        return self

    def rotate(self, angle_deg: float, center: PointLike | None = None) -> Self:
        c = to_point(center or self.center_point)
        self.center_point.rotate(angle_deg, c)
        self.start_angle += angle_deg
        self.end_angle += angle_deg
        return self

    def resize(self, scale_x: float, scale_y: float, center: PointLike | None = None) -> Self:
        c = to_point(center or self.center_point)
        self.center_point.resize(scale_x, scale_y, c)
        self.radius *= (scale_x + scale_y) / 2
        return self

    def mirror(self, point: PointLike = (0, 0), angle: float = 0.0) -> Self:
        self.center_point.mirror(point, angle)
        return self


# ----------------------------------------------------------------------
# Text
# ----------------------------------------------------------------------

@dataclass
class Text(Primitive):
    pos: Point
    content: str = ""

    def __init__(self, pos: PointLike = (0, 0), content: str = "", **kwargs):
        super().__init__(**kwargs)
        self.pos = to_point(pos)
        self.content = content

    def center(self) -> Point:
        return self.pos

    def translate(self, dx: float, dy: float) -> Self:
        self.pos.translate(dx, dy)
        return self

    def rotate(self, angle_deg: float, center: PointLike | None = None) -> Self:
        c = to_point(center or self.pos)
        self.pos.rotate(angle_deg, c)
        return self

    def resize(self, scale_x: float, scale_y: float, center: PointLike | None = None) -> Self:
        c = to_point(center or self.pos)
        self.pos.resize(scale_x, scale_y, c)
        return self

    def mirror(self, point: PointLike = (0, 0), angle: float = 0.0) -> Self:
        self.pos.mirror(point, angle)
        return self


# ----------------------------------------------------------------------
# Group
# ----------------------------------------------------------------------

@dataclass
class Group(Primitive):
    elements: List[Primitive] = field(default_factory=list)

    def add(self, *elements: Primitive) -> None:
        self.elements.extend(elements)

    def center(self) -> Point:
        if not self.elements:
            return Point(0, 0)
        xs, ys = zip(*(e.center() for e in self.elements))
        return Point(sum(xs) / len(xs), sum(ys) / len(ys))

    def translate(self, dx: float, dy: float) -> Self:
        for e in self.elements:
            e.translate(dx, dy)
        return self

    def rotate(self, angle_deg: float, center: PointLike | None = None) -> Self:
        c = to_point(center or self.center())
        for e in self.elements:
            e.rotate(angle_deg, c)
        return self

    def resize(self, scale_x: float, scale_y: float, center: PointLike | None = None) -> Self:
        c = to_point(center or self.center())
        for e in self.elements:
            e.resize(scale_x, scale_y, c)
        return self

    def mirror(self, point: PointLike = (0, 0), angle: float = 0.0) -> Self:
        for e in self.elements:
            e.mirror(point, angle)
        return self
