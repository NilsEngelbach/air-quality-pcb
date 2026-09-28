#!/usr/bin/env python3
"""Prepare a KiCad board for autorouting after a layout/schematic update.

Two cleanup steps that the KiCad MCP does not cover:

1. Remove orphan duplicate footprints.  When a schematic is re-imported, a
   moved part can survive as a second footprint with the same reference but an
   empty schematic path.  The duplicates produce phantom nets (e.g. "GND" next
   to "/GND") that break netclass-aware routing and leave the pour on the wrong
   net.  We drop the copy whose path is empty when the reference is duplicated.

2. Re-target copper zones to the current ground net.  Zones are copied with the
   board and keep the *old* net name, so after the netlist is re-imported the
   GND pour still points at the stale "GND"/"/GND" spelling.  We point every
   ground-named zone at the ground net that actually has pads.

Usage:
    python pcb_prep.py <board.kicad_pcb>

The board is modified in place; back it up first (git).
"""

import sys

import pcbnew


def footprint_path(fp):
    try:
        return fp.GetPath().AsString()
    except Exception:
        return ""


def remove_orphan_duplicates(board):
    """Drop footprints with an empty schematic path whose ref is duplicated by a linked one."""
    by_ref = {}
    for fp in board.GetFootprints():
        by_ref.setdefault(fp.GetReference(), []).append(fp)

    removed = []
    for ref, fps in by_ref.items():
        if len(fps) < 2:
            continue
        linked = [f for f in fps if footprint_path(f)]
        orphans = [f for f in fps if not footprint_path(f)]
        # Only act when we can tell which copy is authoritative.
        if linked and orphans:
            for fp in orphans:
                board.Remove(fp)
                removed.append((ref, pcbnew.ToMM(fp.GetPosition())))
    return removed


def retarget_ground_zones(board):
    """Point ground-named zones at the ground net that has pads."""
    netinfo = board.GetNetInfo()
    ground_nets = [n for n in netinfo.NetsByName().values() if n.GetNetname().endswith("GND")]

    def pad_count(net):
        return sum(1 for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetCode() == net.GetNetCode())

    if not ground_nets:
        return [], None
    target = max(ground_nets, key=pad_count)
    target_name = target.GetNetname()

    changed = []
    for zone in board.Zones():
        name = zone.GetNetname()
        if name.endswith("GND") and name != target_name:
            zone.SetNet(target)
            zone.UnFill()
            changed.append((name, target_name, zone.m_Uuid.AsString()))
    return changed, target_name


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2

    path = sys.argv[1]
    board = pcbnew.LoadBoard(path)

    changed, target = retarget_ground_zones(board)
    removed = remove_orphan_duplicates(board)

    pcbnew.SaveBoard(path, board)

    print(f"board: {path}")
    print(f"removed orphan duplicates: {len(removed)}")
    for ref, pos in removed:
        print(f"  - {ref} at ({pos[0]:.3f}, {pos[1]:.3f})")
    print(f"ground net used for zones: {target}")
    print(f"zones retargeted: {len(changed)}")
    for old, new, uid in changed:
        print(f"  - {old} -> {new}  ({uid})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
