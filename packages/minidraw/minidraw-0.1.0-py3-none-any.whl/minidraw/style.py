from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, List


@dataclass
class Style:
    """Explicit, typed drawing style shared by all primitives and groups."""

    # Basic visual properties
    stroke: Optional[str] = None
    stroke_width: Optional[float] = None
    fill: Optional[str] = None
    opacity: Optional[float] = None

    # Line and dash attributes
    dash: Optional[List[float]] = None
    linecap: Optional[str] = None
    linejoin: Optional[str] = None

    # Text attributes (used by Text primitives)
    font_size: Optional[float] = None
    font_family: Optional[str] = None
    text_anchor: Optional[str] = None

    def merged(self, parent: Optional["Style"] = None) -> "Style":
        """
        Return a new Style inheriting missing attributes from `parent`.
        Fields explicitly set on this style take precedence.
        """
        if parent is None:
            return self

        merged_dict = {**asdict(parent)}
        for key, val in asdict(self).items():
            if val is not None:
                merged_dict[key] = val
        return Style(**merged_dict)
