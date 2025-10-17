from __future__ import annotations
from typing import Iterable, Optional, Union
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from math import sin, cos, radians

from ..primitives import Line, Circle, Rectangle, Polyline, Arc, Text, Group, Primitive
from ..style import Style
from .base import Backend


class SVGBackend(Backend):
    """Render primitives or groups into an SVG string."""

    def __init__(
        self,
        *,
        default_style: Optional[Style] = None,
        pretty_print: bool = False,
        margin: int = 10
    ):
        """
        Parameters
        ----------
        pretty_print:
            Whether to pretty print the XML output with indentation.
        """
        self.pretty_print: bool = pretty_print
        self.default_style: Style = default_style or Style()
        self.margin: int = margin

    # -----------------------------------------------------------
    # Public entry point
    # -----------------------------------------------------------
    def render_to_string(
        self,
        drawable: Primitive | Group | Iterable[Primitive | Group],
    ) -> str:
        drawables = [drawable] if isinstance(drawable, (Primitive, Group)) else list(drawable)

        bounds = self._compute_bounds(drawables)
        if bounds:
            min_x, min_y, max_x, max_y = bounds
        else:
            min_x, min_y, max_x, max_y = -10, -10, 110, 110

        width, height = max_x - min_x, max_y - min_y

        svg = Element(
            "svg",
            xmlns="http://www.w3.org/2000/svg",
            width=str(width),
            height=str(height),
            viewBox=f"{min_x} {min_y} {width} {height}",
        )

        for d in drawables:
            self._draw_item(d, svg, inherited_style=Style())

        svg_bytes = tostring(svg, encoding="utf-8")
        if self.pretty_print:
            parsed = minidom.parseString(svg_bytes)
            return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
        return svg_bytes.decode("utf-8")

    # -----------------------------------------------------------
    # Draw dispatch and primitives
    # -----------------------------------------------------------
    def _draw_item(self, item: Primitive | Group, parent: Element, inherited_style: Style) -> None:
        style = item.style.merged(inherited_style)

        if isinstance(item, Line):
            self._draw_line(item, parent, style)
        elif isinstance(item, Circle):
            self._draw_circle(item, parent, style)
        elif isinstance(item, Rectangle):
            self._draw_rectangle(item, parent, style)
        elif isinstance(item, Polyline):
            self._draw_polyline(item, parent, style)
        elif isinstance(item, Arc):
            self._draw_arc(item, parent, style)
        elif isinstance(item, Text):
            self._draw_text(item, parent, style)
        elif isinstance(item, Group):
            self._draw_group(item, parent, style)

    def _draw_line(self, item: Line, parent: Element, style: Style) -> None:
        x1, y1 = item.start.as_tuple()
        x2, y2 = item.end.as_tuple()
        attrs = {
            "x1": str(x1),
            "y1": str(y1),
            "x2": str(x2),
            "y2": str(y2),
            "stroke": style.stroke or self.default_style.stroke or "black",
            "stroke-width": str(style.stroke_width or self.default_style.stroke_width or 1.0),
            "opacity": str(style.opacity or self.default_style.opacity or 1.0),
        }
        if style.dash:
            attrs["stroke-dasharray"] = " ".join(map(str, style.dash))
        if style.linecap:
            attrs["stroke-linecap"] = style.linecap
        if style.linejoin:
            attrs["stroke-linejoin"] = style.linejoin
        SubElement(parent, "line", attrs)

    def _draw_circle(self, item: Circle, parent: Element, style: Style) -> None:
        cx, cy = item.center_point.as_tuple()
        SubElement(
            parent,
            "circle",
            {
                "cx": str(cx),
                "cy": str(cy),
                "r": str(item.radius),
                "stroke": style.stroke or self.default_style.stroke or "black",
                "fill": style.fill or self.default_style.fill or "none",
                "stroke-width": str(style.stroke_width or self.default_style.stroke_width or 1.0),
                "opacity": str(style.opacity or self.default_style.opacity or 1.0),
            },
        )

    def _draw_rectangle(self, item: Rectangle, parent: Element, style: Style) -> None:
        x, y = item.pos.as_tuple()
        SubElement(
            parent,
            "rect",
            {
                "x": str(x),
                "y": str(y),
                "width": str(item.size[0]),
                "height": str(item.size[1]),
                "stroke": style.stroke or self.default_style.stroke or "black",
                "stroke-width": str(style.stroke_width or self.default_style.stroke_width or 1.0),
                "fill": style.fill or self.default_style.fill or "none",
                "opacity": str(style.opacity or self.default_style.opacity or 1.0),
            },
        )

    def _draw_polyline(self, item: Polyline, parent: Element, style: Style) -> None:
        points_str = " ".join(f"{p.x},{p.y}" for p in item.points)
        attrs = {
            "points": points_str,
            "stroke": style.stroke or self.default_style.stroke or "black",
            "stroke-width": str(style.stroke_width or self.default_style.stroke_width or 1.0),
            "fill": style.fill or self.default_style.fill or "none",
            "opacity": str(style.opacity or self.default_style.opacity or 1.0),
        }
        if style.dash:
            attrs["stroke-dasharray"] = " ".join(map(str, style.dash))
        SubElement(parent, "polyline", attrs)

    def _draw_arc(self, item: Arc, parent: Element, style: Style) -> None:
        cx, cy = item.center_point.as_tuple()
        start_x = cx + item.radius * cos(radians(item.start_angle))
        start_y = cy + item.radius * sin(radians(item.start_angle))
        end_x = cx + item.radius * cos(radians(item.end_angle))
        end_y = cy + item.radius * sin(radians(item.end_angle))
        large_arc_flag = 1 if abs(item.end_angle - item.start_angle) > 180 else 0

        path_d = (
            f"M {start_x},{start_y} "
            f"A {item.radius},{item.radius} 0 {large_arc_flag},1 {end_x},{end_y}"
        )

        SubElement(
            parent,
            "path",
            {
                "d": path_d,
                "stroke": style.stroke or self.default_style.stroke or "black",
                "stroke-width": str(style.stroke_width or self.default_style.stroke_width or 1.0),
                "fill": style.fill or self.default_style.fill or "none",
                "opacity": str(style.opacity or self.default_style.opacity or 1.0),
            },
        )

    def _draw_text(self, item: Text, parent: Element, style: Style) -> None:
        x, y = item.pos.as_tuple()
        text_elem = SubElement(
            parent,
            "text",
            {
                "x": str(x),
                "y": str(y),
                "font-size": str(style.font_size or self.default_style.font_size or 10),
                "font-family": style.font_family or self.default_style.font_family or "sans-serif",
                "text-anchor": style.text_anchor or self.default_style.text_anchor or "start",
                "fill": style.fill or self.default_style.fill or "black",
                "stroke": style.stroke or "none",
                "opacity": str(style.opacity or self.default_style.opacity or 1.0),
            },
        )
        text_elem.text = item.content

    def _draw_group(self, item: Group, parent: Element, inherited_style: Style) -> None:
        group_elem = SubElement(parent, "g")
        for e in item.elements:
            self._draw_item(e, group_elem, inherited_style=item.style.merged(inherited_style))

    # -----------------------------------------------------------
    # Bounding box computation
    # -----------------------------------------------------------
    def _compute_bounds(
        self, elements: Iterable[Primitive | Group]
    ) -> Union[tuple[float, float, float, float], None]:
        xs, ys = [], []

        def collect(item: Primitive | Group):
            if isinstance(item, Line):
                xs.extend([item.start.x, item.end.x])
                ys.extend([item.start.y, item.end.y])
            elif isinstance(item, Circle):
                cx, cy = item.center_point.as_tuple()
                r = item.radius
                xs.extend([cx - r, cx + r])
                ys.extend([cy - r, cy + r])
            elif isinstance(item, Rectangle):
                x, y = item.pos.as_tuple()
                w, h = item.size
                xs.extend([x, x + w])
                ys.extend([y, y + h])
            elif isinstance(item, Polyline):
                for p in item.points:
                    xs.append(p.x)
                    ys.append(p.y)
            elif isinstance(item, Arc):
                cx, cy = item.center_point.as_tuple()
                r = item.radius
                xs.extend([cx - r, cx + r])
                ys.extend([cy - r, cy + r])
            elif isinstance(item, Text):
                x, y = item.pos.as_tuple()
                xs.append(x)
                ys.append(y)
            elif isinstance(item, Group):
                for e in item.elements:
                    collect(e)

        for el in elements:
            collect(el)

        if not xs or not ys:
            return None

        return (min(xs) - self.margin, min(ys) - self.margin, max(xs) + self.margin, max(ys) + self.margin)
