#!/usr/bin/env python3
"""Add a copper keepout ("safe area") around every mounting hole.

A route or via running under a screw head can be shorted or crushed by the
fastener, so each mounting hole gets a circular rule area on both copper layers
where tracks and vias are forbidden (the GND pour is still allowed, so the
plane keeps its integrity).

Re-running is safe: existing keepouts named ``MH_KEEPOUT`` are removed first, so
the board always ends up with exactly one keepout per hole.

Usage:
    python pcb_add_mounting_keepouts.py <board.kicad_pcb> [radius_mm]

The default radius is 3.0 mm (6 mm diameter), comfortably larger than an M2.5
screw head.  The BME688 sensor keepout is also named ``SENSOR_KEEPOUT`` so the
DSN export step can strip just that one.
"""

import math
import re
import sys

import pcbnew

KEEPOUT_NAME = "MH_KEEPOUT"
SENSOR_NAME = "SENSOR_KEEPOUT"


def _circle_points(cx, cy, radius, segments=48):
    return [
        pcbnew.VECTOR2I(
            pcbnew.FromMM(cx + radius * math.cos(2 * math.pi * i / segments)),
            pcbnew.FromMM(cy + radius * math.sin(2 * math.pi * i / segments)),
        )
        for i in range(segments)
    ]


def _name_zone(zone, name):
    try:
        zone.SetZoneName(name)
    except Exception:
        pass


def _is_sensor_keepout(zone):
    """A rule area that only forbids copper pour (the BME688 thermal keepout)."""
    return (
        zone.GetIsRuleArea()
        and not zone.GetDoNotAllowTracks()
        and not zone.GetDoNotAllowVias()
        and zone.GetDoNotAllowZoneFills()
    )


def main():
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        return 2
    path = sys.argv[1]
    radius = float(sys.argv[2]) if len(sys.argv) == 3 else 3.0

    board = pcbnew.LoadBoard(path)

    holes = []
    for fp in board.GetFootprints():
        if re.fullmatch(r"H\d+", fp.GetReference()):
            pos = fp.GetPosition()
            holes.append((fp.GetReference(), pcbnew.ToMM(pos)[0], pcbnew.ToMM(pos)[1]))

    # Remove previous mounting-hole keepouts (idempotent re-run).
    for z in list(board.Zones()):
        if z.GetZoneName() == KEEPOUT_NAME:
            board.Remove(z)

    # Tag the sensor keepout so dsn_strip_zone_keepouts.py can target it.
    named_sensor = 0
    for z in board.Zones():
        if _is_sensor_keepout(z):
            _name_zone(z, SENSOR_NAME)
            named_sensor += 1

    added = 0
    for ref, cx, cy in holes:
        pts = _circle_points(cx, cy, radius)
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            z = pcbnew.ZONE(board)
            z.SetLayer(layer)
            z.SetIsRuleArea(True)
            z.SetDoNotAllowTracks(True)
            z.SetDoNotAllowVias(True)
            z.SetDoNotAllowZoneFills(False)
            z.SetDoNotAllowPads(False)
            z.SetDoNotAllowFootprints(False)
            _name_zone(z, KEEPOUT_NAME)
            outline = z.Outline()
            outline.NewOutline()
            for p in pts:
                outline.Append(p.x, p.y)
            board.Add(z)
            added += 1

    pcbnew.SaveBoard(path, board)
    print(f"board: {path}")
    print(f"mounting holes: {len(holes)} -> keepouts added: {added} (radius {radius} mm)")
    print(f"sensor keepouts named {SENSOR_NAME}: {named_sensor}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
