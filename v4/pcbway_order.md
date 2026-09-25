# PCBWay order config — air-quality-pcb v4 (PROPOSED, not written to repo)

Files: v4/gerbers/*.gtl,.gbl,.gts,.gbs,.gto,.gbo,.gm1 + air-quality-pcb-v4.drl
Dimensions: 72.05 x 72.05 mm, 2 layers

## PCB (Fabrication)
- Board type: Single piece
- Layers: 2
- Dimensions: 72.05 x 72.05 mm (auto from gerber)
- Quantity: 5 (or 10)
- Thickness: 1.6 mm
- Material: FR-4
- Solder mask: Green (color is arbitrary)
- Silkscreen: White
- Surface finish: HASL (lead-free HASL fine)
- Min track/spacing: 6/6 mil minimum (design min = 0.2 mm / 7.9 mil)
- Min hole size: 0.3 mm (design) -> 0.3 mm option
- Copper weight: 1 oz
- Castellations: NO
- Impedance control: NO
- Gold fingers: NO

## Assembly
- Assembly service: Turnkey (parts sourced by PCBWay)
- Sides: TOP only (no bottom paste/parts; B_Paste is empty)
- Qty: same as PCB (5)
- BOM: v4/bom_v4.csv
- Centroid / P&P: generate from KiCad (File > Fabrication Outputs > Component
  Placement .pos); CSV, both sides or top-only
- Board build time: Normal

## Parts / sourcing notes
- BME688 (U5): LGA-8 3x3 mm on-board, matches part number -> Turnkey
- ESP-12F (U1): stocked popular part -> sourceable
- CP2102N-A02-GQFN28 (U2): QFN28, in stock -> sourceable
- USB4175-03-A (J1): not in stock -> approve substitute OR add to "consigned"
  / self-supply. Module is hand-solderable anyway.
- THT parts (J3/J5 headers, J4 LiPo JST) -> either let PCBWay solder them or
  request "no THT assembly" and hand-solder.
- SW3 PCM12 power switch: check stock.

## Pre-flight / risks (verify before upload)
1. BOM has no MPN/manufacturer columns -> PCBWay must match by Value only.
   Non-passive line items (U1,U2,U3,U5,U6,U7, J1, D4, L1) have no supplier P/N.
2. No LCSC/JLCPCB part IDs in schematic.
3. B_Paste is empty = top-side assembly only.
4. Gerber drill reports profile finish "None" -> set finish manually in order.
5. Castellation: not requested. ESP-12F is a module (not a board feature).
