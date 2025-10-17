from minidraw import (
    Drawing,
    Group,
    Style,
    Line,
    Circle,
    Rectangle,
    Polyline,
    Arc,
    Text,
)


def make_demo() -> Drawing:
    d = Drawing()
    y = 0
    section_h = 90

    # ------------------------------------------------------------
    # Helper: label each panel
    # ------------------------------------------------------------
    def label(g: Group, pos, text: str):
        g.add(
            Text(
                pos,
                text,
                style=Style(
                    font_size=12,
                    fill="black",
                    stroke="none",
                    text_anchor="start",
                ),
            )
        )

    # ------------------------------------------------------------
    # Helper: create section group
    # ------------------------------------------------------------
    def section(title: str) -> Group:
        nonlocal y
        g = Group()
        d.add(g)
        label(g, (10, y + 10), title.upper())
        y += section_h
        return g

    # ============================================================
    # 1. Translation
    # ============================================================
    g = section("Translation")

    base = Rectangle((20, y - 60), (30, 20)).set_style(Style(stroke="#999"))
    moved = base.copy().translate(60, 0).set_style(Style(stroke="red"))
    g.add(base, moved)
    label(g, (60, y - 30), "translated")

    # ============================================================
    # 2. Rotation
    # ============================================================
    g = section("Rotation")

    base = Line((30, y - 50), (60, y - 80)).set_style(Style(stroke="#999"))
    rotated = base.copy().rotate(45, (45, y - 65)).set_style(Style(stroke="blue"))
    g.add(base, rotated)
    label(g, (70, y - 60), "rotated 45°")

    # ============================================================
    # 3. Scaling
    # ============================================================
    g = section("Scaling")

    base = Circle((40, y - 40), 10).set_style(Style(stroke="#999"))
    scaled = base.copy().scale(1.8).set_style(Style(stroke="green"))
    g.add(base, scaled)
    label(g, (70, y - 40), "scaled ×1.8")

    # ============================================================
    # 4. Mirroring
    # ============================================================
    g = section("Mirroring")

    base = Rectangle((20, y - 60), (30, 20)).set_style(Style(stroke="#999"))
    mirrored_v = base.copy().mirror_vertical(50).set_style(Style(stroke="orange"))
    mirrored_h = base.copy().mirror_horizontal(y - 50).set_style(Style(stroke="purple"))
    g.add(base, mirrored_v, mirrored_h)
    label(g, (70, y - 50), "mirrored vertical + horizontal")

    # ============================================================
    # 5. Polyline
    # ============================================================
    g = section("Polyline Transformation")

    poly = Polyline([(20, y - 40), (40, y - 60), (60, y - 40)]).set_style(
        Style(stroke="#999", fill="none")
    )
    poly2 = poly.copy().rotate(30, (40, y - 50)).set_style(Style(stroke="brown"))
    g.add(poly, poly2)
    label(g, (70, y - 50), "rotated 30°")

    # ============================================================
    # 6. Arc
    # ============================================================
    g = section("Arc Transformation")

    base = Arc((40, y - 40), radius=15, start_angle=0, end_angle=90).set_style(
        Style(stroke="#999", fill="none")
    )
    arc2 = base.copy().rotate(45, (40, y - 40)).set_style(Style(stroke="teal"))
    g.add(base, arc2)
    label(g, (70, y - 40), "rotated 45°")

    # ============================================================
    # 7. Group Transformation
    # ============================================================
    g = section("Group Transformation")

    sub = Group()
    sub.add(
        Circle((40, y - 40), 10),
        Rectangle((30, y - 50), (20, 20)),
        Text((40, y - 25), "A", style=Style(font_size=10, fill="black")),
    )
    sub2 = sub.copy().rotate(30, (40, y - 40)).set_style(Style(stroke="blue"))
    g.add(sub, sub2)
    label(g, (70, y - 40), "group rotated 30°")

    return d


def main():
    drawing = make_demo()
    drawing.render_to_file("spatial_transforms_demo.svg")
    print("✅ Wrote spatial_transforms_demo.svg")
    print(drawing.render_to_string("python"))


if __name__ == "__main__":
    main()
