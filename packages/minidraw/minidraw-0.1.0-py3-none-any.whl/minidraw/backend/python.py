from __future__ import annotations
from typing import List
from pathlib import Path
from ..primitives import (
    Primitive,
    Group,
    Line,
    Circle,
    Rectangle,
    Polyline,
    Arc,
    Text,
)
from ..style import Style


class PythonBackend:
    """Backend that generates clean, runnable Python code reproducing a drawing."""

    def __init__(
        self,
        ignore_style: bool = False,
        standalone: bool = True,
    ):
        """
        Args:
            ignore_style: If True, omit all style arguments (geometry only).
            standalone: If False, omit imports/header/footer — produce only drawing code.
        """
        self.ignore_style = ignore_style
        self.standalone = standalone
        self.group_counter = 0

    # ------------------------------------------------------------------
    # Rendering entrypoints
    # ------------------------------------------------------------------
    def render_to_string(self, elements: List[Primitive]) -> str:
        lines: List[str] = []

        # Header -------------------------------------------------------
        if self.standalone:
            lines += [
                "from minidraw import Drawing, Group, Style, Line, Circle, Rectangle, Polyline, Arc, Text",
                "",
                "d = Drawing()",
            ]

        # Body ---------------------------------------------------------
        for e in elements:
            lines.extend(self._render_primitive(e, var_prefix="d"))

        # Footer -------------------------------------------------------
        if self.standalone:
            lines += [
                "",
                "d.render_to_file('output.svg')",
            ]

        return "\n".join(lines)

    def render_to_file(self, path: Path, elements: List[Primitive]) -> None:
        path.write_text(self.render_to_string(elements), encoding="utf-8")

    # ------------------------------------------------------------------
    # Primitive rendering
    # ------------------------------------------------------------------
    def _render_primitive(self, p: Primitive, var_prefix: str) -> List[str]:
        lines: List[str] = []

        # --- Group ----------------------------------------------------
        if isinstance(p, Group):
            self.group_counter += 1
            gname = f"g{self.group_counter}"
            style_part = self._style_arg(p.style)
            style_text = f"({style_part})" if style_part else "()"
            lines.append(f"{gname} = Group{style_text}")
            for e in p.elements:
                lines.extend(self._render_primitive(e, var_prefix=gname))
            lines.append(f"{var_prefix}.add({gname})")
            return lines

        # --- Line -----------------------------------------------------
        if isinstance(p, Line):
            args = f"({p.start.x}, {p.start.y}), ({p.end.x}, {p.end.y})"
            lines.append(f"{var_prefix}.add(Line({args}{self._style_suffix(p)}))")
            return lines

        # --- Circle ---------------------------------------------------
        if isinstance(p, Circle):
            args = f"({p.center_point.x}, {p.center_point.y}), {p.radius}"
            lines.append(f"{var_prefix}.add(Circle({args}{self._style_suffix(p)}))")
            return lines

        # --- Rectangle ------------------------------------------------
        if isinstance(p, Rectangle):
            args = f"({p.pos.x}, {p.pos.y}), ({p.size[0]}, {p.size[1]})"
            lines.append(f"{var_prefix}.add(Rectangle({args}{self._style_suffix(p)}))")
            return lines

        # --- Polyline -------------------------------------------------
        if isinstance(p, Polyline):
            pts = ", ".join(f"({pt.x}, {pt.y})" for pt in p.points)
            lines.append(f"{var_prefix}.add(Polyline([{pts}]{self._style_suffix(p)}))")
            return lines

        # --- Arc ------------------------------------------------------
        if isinstance(p, Arc):
            args = f"({p.center_point.x}, {p.center_point.y}), {p.radius}, {p.start_angle}, {p.end_angle}"
            lines.append(f"{var_prefix}.add(Arc({args}{self._style_suffix(p)}))")
            return lines

        # --- Text -----------------------------------------------------
        if isinstance(p, Text):
            text_value = repr(p.content)
            args = f"({p.pos.x}, {p.pos.y}), {text_value}"
            lines.append(f"{var_prefix}.add(Text({args}{self._style_suffix(p)}))")
            return lines

        return lines

    # ------------------------------------------------------------------
    # Style formatting
    # ------------------------------------------------------------------
    def _style_suffix(self, p: Primitive) -> str:
        """Return formatted style suffix like ', style=Style(...)' or empty string."""
        if self.ignore_style:
            return ""
        style_str = self._style_arg(p.style)
        return f", style={style_str}" if style_str else ""

    def _style_arg(self, style: Style) -> str:
        """Return 'Style(...)' string if style has at least one non-None value."""
        if self.ignore_style or style is None:
            return ""

        args = []
        if style.stroke is not None:
            args.append(f"stroke={style.stroke!r}")
        if style.stroke_width is not None:
            args.append(f"stroke_width={style.stroke_width}")
        if style.fill is not None:
            args.append(f"fill={style.fill!r}")
        if style.opacity is not None:
            args.append(f"opacity={style.opacity}")
        if style.dash is not None:
            args.append(f"dash={style.dash}")
        if style.linecap is not None:
            args.append(f"linecap={style.linecap!r}")
        if style.linejoin is not None:
            args.append(f"linejoin={style.linejoin!r}")
        if style.font_size is not None:
            args.append(f"font_size={style.font_size}")
        if style.font_family is not None:
            args.append(f"font_family={style.font_family!r}")
        if style.text_anchor is not None:
            args.append(f"text_anchor={style.text_anchor!r}")

        if not args:
            return ""
        return f"Style({', '.join(args)})"
