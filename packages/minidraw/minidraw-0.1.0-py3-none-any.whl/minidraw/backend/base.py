from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable
from ..primitives import Primitive, Group


class Backend(ABC):
    """Abstract base class for all rendering backends."""

    @abstractmethod
    def render_to_string(
        self,
        drawable: Primitive | Group | Iterable[Primitive | Group],
    ) -> str:
        """Render primitives or groups and return backend-specific output as a string."""
        raise NotImplementedError(
            f"Backend {self.__class__.__name__} does not support text rendering; use render_to_file instead."
        )

    def render_to_file(
        self,
        path: Path ,
        drawable: Primitive | Group | Iterable[Primitive | Group],
    ) -> None:
        """Render primitives or groups to a file.

        By default, this calls `render_to_string` and writes the result to disk.
        Backends that do not produce text output (e.g., raster backends) should
        override this method directly.
        """
        content = self.render_to_string(drawable)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
