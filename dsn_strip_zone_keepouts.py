#!/usr/bin/env python3
"""Strip a named copper-pour keepout from a KiCad-exported Specctra DSN.

KiCad's Specctra export turns a copper-zone keepout (a zone whose only
restriction is ``copperpour not_allowed``) into a hard DSN keepout that
Freerouting treats as off-limits for *tracks and vias too*.  Pads sitting
inside that zone (e.g. a fine-pitch sensor under a vent/thermal keepout) then
cannot be fanned out and stay unrouted, even though KiCad explicitly allows
tracks and vias there.

Removing that keepout from the DSN lets the router reach those pads.  The
keepout stays in the ``.kicad_pcb``, so the final zone refill still refuses to
pour copper there.

Only the sensor keepout is removed: it is a rectangle (few vertices), whereas
the mounting-hole safe areas (added by ``pcb_add_mounting_keepouts.py``) are
polygonised circles with dozens of vertices, so the router still avoids them.

Usage:
    python dsn_strip_zone_keepouts.py in.dsn [out.dsn] [max_points]

With no output path the file is rewritten in place.  ``max_points`` defaults to
8 (rectangles/quads and simpler); raise it only if the sensor keepout is drawn
with more vertices.
"""

import re
import sys


def _expr_end(text, start):
    depth = 0
    in_string = False
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '"':
            in_string = not in_string
        elif in_string:
            continue
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i + 1
    return -1


def _structure_span(text):
    m = re.search(r"\(structure\b", text)
    if not m:
        return None
    end = _expr_end(text, m.start())
    return (m.start(), end) if end > 0 else None


_KEEPOUT = re.compile(r'\(keepout\s+"[^"]*"\s+\(polygon\s+[FB]\.Cu\b')


def _point_count(expr):
    """Number of coordinate pairs inside a keepout (polygon ...) expression."""
    nums = re.findall(r"[-+]?\d+(?:\.\d+)?", expr.split("(polygon", 1)[1])
    # First token after the layer name is the polygon's "0" index; the rest are x/y.
    return max(0, (len(nums) - 1) // 2)


def strip(text, max_points):
    """Remove board-level copper keepouts with at most ``max_points`` vertices.

    The sensor keepout is a rectangle (few points); the mounting-hole safe areas
    are polygonised circles (dozens of points) and are kept.
    """
    span = _structure_span(text)
    if not span:
        return text, 0
    start, end = span
    head, body, tail = text[:start], text[start:end], text[end:]

    removed = 0
    out = []
    pos = 0
    while True:
        m = _KEEPOUT.search(body, pos)
        if not m:
            out.append(body[pos:])
            break
        expr_end = _expr_end(body, m.start())
        if expr_end < 0:
            out.append(body[pos:])
            break
        expr = body[m.start():expr_end]
        out.append(body[pos : m.start()])
        if 0 < _point_count(expr) <= max_points:
            removed += 1
        else:
            out.append(expr)
        pos = expr_end
    return head + "".join(out) + tail, removed


def main():
    if len(sys.argv) not in (2, 3, 4):
        print(__doc__)
        return 2
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) >= 3 else src
    max_points = int(sys.argv[3]) if len(sys.argv) == 4 else 8
    text = open(src, encoding="utf-8").read()
    stripped, removed = strip(text, max_points)
    if removed:
        open(dst, "w", encoding="utf-8").write(stripped)
    print(f"{src}: removed {removed} rectangular keepout(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
