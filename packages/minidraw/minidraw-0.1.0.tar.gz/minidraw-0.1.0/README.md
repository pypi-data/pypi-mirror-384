# minidraw

**minidraw** is a minimal, pure-Python 2D drawing library designed around composable geometric primitives and spatial transformations. It enables you to build structured vector graphics, transform them fluently, and export them into multiple formats such as **SVG** or **Python code**.

---

## ✨ Features

* **Composable primitives**: Line, Circle, Rectangle, Polyline, Arc, and Text.
* **Hierarchical grouping** with transformation inheritance.
* **Fluent spatial transformations** — translate, rotate, scale, and mirror any element.
* **Declarative styling** using the `Style` dataclass.
* **Multiple rendering backends**:
  * `SVGBackend` → export as `.svg`
  * `PythonBackend` → generate equivalent Python source code.
* **Simple, readable API** that keeps math and rendering separate.

---

## 🧱 Core Modules

| Module          | Description                                                |
| --------------- | ---------------------------------------------------------- |
| `point.py`      | Defines `Point`, a transformable 2D coordinate class.      |
| `spatial.py`    | Abstract base class defining the transformation interface. |
| `primitives.py` | Geometric shapes and `Group` container.                    |
| `style.py`      | Explicit visual style dataclass shared by primitives.      |
| `transform.py`  | Math helpers for rotation, scaling, and mirroring.         |
| `drawing.py`    | Top-level `Drawing` object with backend rendering.         |

---

## 🧩 Basic Example

```python
from minidraw import Drawing, Line, Circle, Style

d = Drawing()

# Add some primitives
l = Line((10, 10), (80, 80), style=Style(stroke="black"))
c = Circle((50, 50), 20, style=Style(stroke="red", fill="none"))

d.add(l, c)

# Apply transformations
c.copy().translate(40, 0).scale(1.2)

# Export
print(d.render_to_string("python"))   # → Python code output
d.render_to_file("example.svg")       # → SVG file
```

---

## 🔄 Transformations

All primitives implement:

* `translate(dx, dy)` – move by offset.
* `rotate(angle, center=None)` – rotate around a point.
* `resize(sx, sy, center=None)` – scale along axes.
* `scale(factor, center=None)` – uniform scale.
* `mirror(point, angle)` – reflect across an arbitrary line.
* `mirror_vertical(x)` / `mirror_horizontal(y)` – convenient reflections.

Transformations mutate the object in place, but `copy()` creates deep copies for safe chaining.

---

## 🎨 Styling

The `Style` dataclass allows fine-grained control over stroke, fill, text, and opacity:

```python
Style(
    stroke="black",
    stroke_width=2.0,
    fill="none",
    opacity=0.8,
    font_size=14,
    text_anchor="middle",
)
```

`Style` objects can be merged using `.merged(parent)` to inherit defaults.

---

## 🧠 Example: Spatial Transform Demo

`demo_spatial_transforms.py` showcases all core transformations:

```python
from minidraw import Drawing, Rectangle, Circle, Line, Polyline, Arc, Text, Style, Group

d = Drawing()
g = Group()

base = Rectangle((10, 10), (30, 20), style=Style(stroke="#999"))
rotated = base.copy().rotate(30, (25, 20)).set_style(Style(stroke="red"))

g.add(base, rotated)
d.add(g)

d.render_to_file("spatial_transforms_demo.svg")
```

Produces an SVG illustrating translation, rotation, scaling, and mirroring.

---

## 🧰 Backends

* **`SVGBackend`** – converts primitives into valid SVG markup.
* **`PythonBackend`** – generates equivalent Python code that recreates the drawing.

Custom backends can be implemented by subclassing `Backend` and overriding:

```python
def render_to_string(self, elements: list[Primitive]) -> str:
    ...

def render_to_file(self, path: Path, elements: list[Primitive]) -> None:
    ...
```

---

## 📦 Installation

```bash
pip install minidraw
```

*(for now, clone and install locally until released on PyPI)*

```bash
git clone https://github.com/yourname/minidraw.git
cd minidraw
pip install -e .
```

---

## 🧾 License

MIT License © 2025 — Designed for simplicity and educational clarity.
