from math import cos, sin, radians


def rotate_point(p: tuple[float, float], angle_deg: float, center: tuple[float, float]) -> tuple[float, float]:
    x, y = p
    cx, cy = center
    angle = radians(angle_deg)
    dx, dy = x - cx, y - cy
    return (
        cx + dx * cos(angle) - dy * sin(angle),
        cy + dx * sin(angle) + dy * cos(angle),
    )


def scale_point(p: tuple[float, float], scale_x: float, scale_y: float, center: tuple[float, float]) -> tuple[float, float]:
    x, y = p
    cx, cy = center
    return (cx + (x - cx) * scale_x, cy + (y - cy) * scale_y)


def mirror_point(
    p: tuple[float, float],
    *,
    vertical: bool = False,
    horizontal: bool = False,
    center: tuple[float, float] = (0, 0),
) -> tuple[float, float]:
    """Mirror a point across a vertical and/or horizontal axis passing through `center`."""
    x, y = p
    cx, cy = center
    if vertical:
        x = 2 * cx - x
    if horizontal:
        y = 2 * cy - y
    return (x, y)


def mirror_point_angle(
    p: tuple[float, float],
    point: tuple[float, float],
    angle_deg: float,
) -> tuple[float, float]:
    """Reflect a point `p` across a line passing through `point` at orientation `angle_deg` (degrees)."""
    x, y = p
    px, py = point
    a = radians(angle_deg)

    # Step 1: translate so line passes through origin
    dx, dy = x - px, y - py

    # Step 2: rotate so line aligns with x-axis
    x_rot = dx * cos(a) + dy * sin(a)
    y_rot = -dx * sin(a) + dy * cos(a)

    # Step 3: mirror across x-axis (flip y)
    y_rot = -y_rot

    # Step 4: rotate back and translate back
    x_new = x_rot * cos(a) - y_rot * sin(a) + px
    y_new = x_rot * sin(a) + y_rot * cos(a) + py

    return (x_new, y_new)
