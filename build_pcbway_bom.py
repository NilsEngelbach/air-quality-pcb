"""Build PCBWay-format BOM from the KiCad BOM export.

Usage:  python build_pcbway_bom.py [version]     (default: v5)

Step 1 (KiCad, MCP tool export_sch_bom): export the schematic BOM ungrouped
with fields Reference,Value,Footprint,Manufacturer,MPN,Description to
v<version>/bom_kicad_raw.csv
Step 2 (this script): aggregate to PCBWay columns:
Item #, *Designator, *Qty, Manufacturer, *Mfg Part #, Description / Value,
*Package/Footprint, Type, Notes
"""
import csv
import re
import sys
from collections import OrderedDict
from pathlib import Path

VER = sys.argv[1] if len(sys.argv) > 1 else "v5"
HERE = Path(__file__).resolve().parent
SRC = str(HERE / VER / "bom_kicad_raw.csv")
DST = str(HERE / VER / f"bom_pcbway_{VER}.csv")

# short package names for the *Package/Footprint column
PKG = {
    "Capacitor_SMD:C_0805_2012Metric": "0805",
    "Capacitor_SMD:CP_Elec_6.3x5.4": "6.3x5.4mm SMD V-chip",
    "Resistor_SMD:R_0805_2012Metric": "0805",
    "Diode_SMD:D_SOD-123": "SOD-123",
    "Diode_SMD:D_SMA": "SMA (DO-214AC)",
    "LED_SMD:LED_0805_2012Metric": "0805",
    "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12": "USB-C 16P mid-mount",
    "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical": "1x03 2.54mm",
    "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical": "1x04 2.54mm",
    "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical": "JST PH 2mm 1x02",
    "Inductor_SMD:L_Sunlord_SWPA4030S": "SWPA4030S (4x4x3)",
    "Package_TO_SOT_SMD:SOT-23": "SOT-23",
    "Package_TO_SOT_SMD:SOT-23-5": "SOT-23-5",
    "Package_TO_SOT_SMD:SOT-23-6": "SOT-23-6",
    "Package_DFN_QFN:QFN-28-1EP_5x5mm_P0.5mm_EP3.35x3.35mm": "QFN-28 5x5",
    "Package_LGA:Bosch_LGA-8_3x3mm_P0.8mm_ClockwisePinNumbering": "LGA-8 3x3",
    "RF_Module:ESP-12E": "ESP-12 module",
    "Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2": "KMR2 (4.2x2.8mm)",
    "Button_Switch_SMD:SW_SPDT_PCM12": "PCM12",
    "Button_Switch_SMD:SW_SP3T_PCM13": "PCM13",
    "LED_SMD:LED_Kingbright_KPA-3010_3x2x1mm": "3.0x2.0x1.0mm side-view",
    "Power_Protection:USBLC6-2SC6": "SOT-23-6",
    "AirQuality:ESP32-C3-WROOM-02_EPADvia0.3": "ESP32-C3-WROOM-02 module 18x20mm",
    "Button_Switch_THT:SW_Slide_SPDT_Angled_CK_OS102011MA1Q": "C&K OS right-angle SPDT (THT)",
    "AirQuality:SW_Slide_SP3T_Angled_CK_OS103011MA7Q": "C&K OS right-angle SP3T (THT)",
    "Diode_SMD:Nexperia_CFP3_SOD-123W": "SOD-123W (CFP3)",
    "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal": "JST SH 1.0mm 4P right-angle SMD",
}

THT_FP = (
    "Connector_PinHeader_2.54mm:",
    "Connector_JST:",
    "Button_Switch_THT:",
    "AirQuality:SW_Slide_",
)

NOTES = {
    "LTST-C170TBKT": "Blue status LED (color was unspecified in schematic)",
    "PCM12SMTBR": "Active replacement for obsolete PCM12SMTR; same PCM12 series/land",
    "UCD1C101MCL1GS": "6.3mm dia, 5.8mm height - fits CP_Elec_6.3x5.4 land",
    "ESP-12F": "ESP8266 module; e.g. LCSC C82891",
    "TYPE-C-31-M-12": "e.g. LCSC C165948",
    "MT3608": "e.g. LCSC C84717",
    "CP2102N-A02-GQFN28": "Tape-and-reel: CP2102N-A02-GQFN28R",
    "ESP32-C3-WROOM-02-N4": "ESP32-C3 module, 4 MB flash; EPAD thermal vias 0.3 mm",
    "OS102011MA1QN1": "Right-angle THT, 4 mm actuator; e.g. LCSC C226259",
    "OS103011MA7QP1": "Right-angle THT SP3T, 4 mm actuator; Digi-Key CKN9561-ND; custom footprint - verify",
    "PMEG4030ER,115": "Replaces SS34 (SMA) for a smaller boost loop",
    "SM04B-SRSS-TB(LF)(SN)": "STEMMA QT / Qwiic port",
    "KPA-3010SGC": "Green side-view charge LED",
}

def refkey(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2)))

groups = OrderedDict()
with open(SRC, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        ref = row["Reference"].strip()
        if not row["MPN"].strip():          # JP1 solder jumper: no part -> skip
            continue
        key = (row["Manufacturer"].strip(), row["MPN"].strip())
        groups.setdefault(key, []).append(row)

rows = []
for (mfr, mpn), items in groups.items():
    refs = sorted((r["Reference"].strip() for r in items), key=refkey)
    fp = items[0]["Footprint"]
    ptype = "THT" if fp.startswith(THT_FP) and "_SM0" not in fp else "SMD"  # JST SH SMxxB = SMD
    desc = items[0]["Description"] or items[0]["Value"]
    rows.append({
        "refs": refs,
        "mfr": mfr,
        "mpn": mpn,
        "desc": desc,
        "pkg": PKG.get(fp, fp.split(":")[-1]),
        "type": ptype,
        "note": NOTES.get(mpn, ""),
        "sort": refkey(refs[0]),
    })

rows.sort(key=lambda r: r["sort"])

with open(DST, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Item #", "*Designator", "*Qty", "Manufacturer", "*Mfg Part #",
                "Description / Value", "*Package/Footprint", "Type",
                "Your Instructions / Notes"])
    for i, r in enumerate(rows, 1):
        w.writerow([i, ", ".join(r["refs"]), len(r["refs"]), r["mfr"], r["mpn"],
                    r["desc"], r["pkg"], r["type"], r["note"]])

print(f"wrote {DST} with {len(rows)} rows, "
      f"{sum(len(r['refs']) for r in rows)} placements")
