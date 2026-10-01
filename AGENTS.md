# AGENTS.md

## Re-routing and refilling a revised board (KiCad + kicad MCP)

The PCB layout changes often. After moving parts, the board's traces are stale
and the GND pours must be refilled. This is the procedure. It is written for the
`kicad` MCP server, with two small helper scripts for the steps the MCP does not
cover.

### One-time setup (only if the `kicad_*` MCP tools are missing)

The MCP server runs KiCad's **bundled** Python, which does not ship the server's
dependencies. Install them once (and again after a KiCad upgrade):

```sh
"C:/Program Files/KiCad/10.0/bin/python.exe" -m pip install --user -r C:/DEV/KiCAD-MCP-Server/requirements.txt
```

Verify by restarting the MCP and listing tools (`get_board_info` should work).
Freerouting needs `~/.kicad-mcp/freerouting.jar` and the Java release the JAR was
built for (2.4.x → Java 25); check with the `check_freerouting` tool.

### Procedure

Run each numbered step for the target board, e.g.
`v5/air-quality-pcb-v5.kicad_pcb`. Tool names are MCP tools; commands in `sh`
blocks run in the shell.

**0. Prep the board** (removes orphan/duplicate footprints and re-points ground
zones at the current ground net). The MCP cannot do either of these:

```sh
"/c/Program Files/KiCad/10.0/bin/python.exe" pcb_prep.py v5/air-quality-pcb-v5.kicad_pcb
```

**1. Open the board and clear the old routing** — `open_board`, then
`delete_trace` with `net="*"` and `includeVias=true`.

**2. Fill the GND pours before routing** so Freerouting only has to route
signals: `open_board` → `refill_zones` → `save_board {force:true}`.

**3. Autoroute the signals.** The straightforward path is the MCP `autoroute`
tool (`maxPasses` 30, `timeout` 600). Use the manual path below when the board
has a copper-pour keepout (see *Why*):

```sh
# a) export the current board to Specctra DSN
#    MCP: open_board -> export_dsn {outputPath: route.dsn}
# b) let Freerouting route inside copper-pour keepouts (KiCad allows tracks there)
"/c/Program Files/KiCad/10.0/bin/python.exe" dsn_strip_zone_keepouts.py route.dsn
# c) route; -mt 1 avoids the multi-threaded optimiser's clearance violations
java -jar ~/.kicad-mcp/freerouting.jar -de route.dsn -do route.ses \
  --gui.enabled=false -mp 40 -mt 1
# d) import the result (reconciles '/'-prefixed net names automatically)
#    MCP: open_board -> import_ses {sesPath: route.ses}
```

**4. Fill the pours again and save** (step 2), because routing cuts the copper.

**5. Check:** `run_drc`. `unconnected_items` means a net was not fully routed;
`clearance` means tracks are too close; `track_width` means a segment is thinner
than the board minimum (see *Track width*).

**6. Stitch the ground:** `add_gnd_stitching_vias` with
`strategies:["grid","around_refs","in_zones"]`, `densifyRefs:["U1","U4","U7"]`.
This ties the pour islands together (`unconnected ... Zone [/GND]` errors).

**7. Fabrication outputs:** `export_gerber` (and `run_erc` for the schematic).

### Fabrication BOM for PCBWay

The schematic carries hidden `Manufacturer`, `MPN` and `Description` properties on
every placed component (verified against Digi-Key). To regenerate the assembly BOM:

1. MCP `export_sch_bom` on the `.kicad_sch`, ungrouped, fields
   `Reference,Value,Footprint,Manufacturer,MPN,Description` → `v5/bom_kicad_raw.csv`.
2. `python build_pcbway_bom.py v5` aggregates it into `v5/bom_pcbway_v5.csv` with
   PCBWay's columns (`*Designator`, `*Qty`, `*Mfg Part #`, `*Package/Footprint`,
   `Type` SMD/THT, Notes). Rows without an MPN (JP1 solder jumper) are excluded.

### Gotchas

- **One mutating MCP call per session.** Each mutating tool auto-saves and the
  auto-save guard then sees the on-disk file as "changed externally" for the
  next mutation in the same session, refusing to save. Reopen the board before
  each mutation, or end the sequence with `save_board {force:true}`.
- **Freerouting ignores project net classes unless they are applied.**
  `autoroute`/`export_dsn` read them from the `.kicad_pro` next to the board;
  export the DSN from the board's own directory.
- **Copper-pour keepouts are exported to the DSN as hard keepouts.** Pads inside
  one (the BME688 sensor zone) cannot fan out and stay unrouted. Step 3b removes
  it from the DSN only; the keepout remains in the board for the refill.
- **Freerouting stops with one net left when the routing channel is too narrow**
  rather than reporting a geometry error. Open a second channel by moving the
  blocking part (for v5 that is C13, see below), then re-route.
- **`refill_zones` can be flaky under the SWIG backend.** Always follow it with
  `save_board {force:true}` and confirm with `query_zones` (`isFilled`).
- **`delete_trace` needs `net:"*"`** to clear everything; the MCP has no
  `delete_zone`, which is why zone work goes through `pcb_prep.py`.
- **MCP schematic edits can delete required junctions.** `batch_connect`,
  `batch_add_and_connect`, `move_schematic_component` and `add_schematic_component`
  run a junction sync that removes junctions where a wire end meets the middle of
  another wire (T-joints). In KiCad those junctions are electrical, so nets silently
  split. After any MCP schematic edit, run `kicad-cli sch erc` and diff the
  junctions against the previous file. `batch_connect` may also draw diagonal wires to
  a "nearby facing label" — check the view.
- **`sync_schematic_to_board` only adds footprints and sets pad nets.** It does not
  remove deleted parts or swap changed footprints, and its own netlist parser names
  nets without KiCad's `/` prefix and misses T-joint connections. Delete the
  removed or changed footprints with pcbnew first, run the sync to add the new ones, then
  re-apply nets, values and paths from `kicad-cli sch export netlist --format kicadxml`.
  Confirm with `kicad-cli pcb drc --schematic-parity`.
- **Large MCP batches can truncate the schematic.** The MCP kills its Python worker
  after 30 s. If `batch_add_and_connect` (or `batch_connect`) is still writing at that moment, the
  `.kicad_sch` is left at **0 bytes**. Keep batches to 2–3 components and copy the file before each call.
- **Text with line breaks:** `add_schematic_text` stores `\n` as a literal
  backslash-n; fix it in the file (`\\n` → `\n`).
- **Project footprints** live in `<version>/AirQuality.pretty` (registered in the
  version's `fp-lib-table`). For v7, update `densifyRefs` in step 6 to the module/regulators
  that exist (`U1`, `U4`, `U7`).
- **BOM without the MCP:** `kicad-cli sch export bom --fields
  "Reference,Value,Footprint,Manufacturer,MPN,Description" --group-by ""` produces
  the same `bom_kicad_raw.csv` that `build_pcbway_bom.py` expects.
