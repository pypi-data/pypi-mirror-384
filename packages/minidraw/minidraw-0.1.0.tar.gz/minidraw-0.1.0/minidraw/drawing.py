# drawing.py
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union, Optional

from .primitives import Group
from .style import Style
from .backend import Backend, SVGBackend, PythonBackend


@dataclass
class Drawing(Group):
    """Top-level drawing — transformable group with rendering capability."""

    default_style: Style = field(default_factory=Style)

    def render_to_file(self, path: Union[Path, str], engine: Optional[Union[str, Backend]] = None) -> None:
        path = Path(path)
        backend = self._to_backend(engine or path)
        backend.render_to_file(path, self.elements)

    def render_to_string(self, engine: str | Backend = "svg") -> str:
        backend = self._to_backend(engine)
        return backend.render_to_string(self.elements)

    def _to_backend(self, engine: str | Backend | Path) -> Backend:
        if isinstance(engine, Backend):
            return engine
        if isinstance(engine, Path):
            engine = engine.suffix
        if engine in ["svg", ".svg"]:
            return SVGBackend(pretty_print=True)
        elif engine in ["python", "py", ".py"]:
            return PythonBackend()
        raise NotImplementedError(f"Unknown backend: {engine}")
