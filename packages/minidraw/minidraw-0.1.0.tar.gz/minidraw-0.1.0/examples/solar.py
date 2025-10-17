from math import cos, sin, radians
from minidraw import Drawing, Style

# ------------------------------------------------------------
# Create a new drawing
# ------------------------------------------------------------
d = Drawing()

# --- Sun ---
sun_style = Style(
    fill="gold",
    stroke="orange",
    stroke_width=2,
    opacity=0.95,
)
d.circle(center=(0, 0), radius=20, style=sun_style)
d.text(
    pos=(0, 30),
    content="Sun",
    style=Style(
        fill="black",
        font_size=8,
        text_anchor="middle",
    ),
)

# --- Orbits ---
orbit_style = Style(
    stroke="gray",
    stroke_width=0.5,
    dash=[2, 2],
    opacity=0.5,
    fill="none",
)
for r in [40, 70, 100]:
    d.circle(center=(0, 0), radius=r, style=orbit_style)

# --- Planets ---
planets = [
    {"name": "Mercury", "radius": 3, "dist": 40, "angle": 45, "color": "#b0b0b0"},
    {"name": "Venus", "radius": 5, "dist": 70, "angle": 120, "color": "#e0b060"},
    {"name": "Earth", "radius": 6, "dist": 100, "angle": 200, "color": "#4a90e2"},
]

for p in planets:
    x = p["dist"] * cos(radians(p["angle"]))
    y = p["dist"] * sin(radians(p["angle"]))

    planet_style = Style(fill=p["color"], stroke="black")
    d.circle((x, y), p["radius"], style=planet_style)

    d.text(
        pos=(x, y + p["radius"] + 6),
        content=p["name"],
        style=Style(
            fill="black",
            font_size=6,
            text_anchor="middle",
        ),
    )

# ------------------------------------------------------------
# Render output
# ------------------------------------------------------------
d.render_to_file("solar_system.svg")
d.render_to_file("solar.py")

