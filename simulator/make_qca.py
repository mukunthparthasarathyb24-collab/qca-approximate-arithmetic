"""Generate QCADesigner(-E) .qca files for the Seyedi & Abdoli (2024) layouts.

Grid: 20 nm pitch, 18x18 nm cells (QCADesigner default).
Coordinates are (col, row) read off Figs 5b, 6b, 7b and 9 of the paper.
Clock zones: 0 = green, 1 = purple, 2 = blue, 3 = white (paper colours).
"""
import os

PITCH = 20.0
X0, Y0 = 200.0, 200.0
QHALF = 8.010882e-20          # half an electron charge per dot = unpolarised


def cell(col, row, clock, func="NORMAL", label=None):
    return dict(col=col, row=row, clock=clock, func=func, label=label)


def cell_text(c):
    x = X0 + c["col"] * PITCH
    y = Y0 + c["row"] * PITCH
    rgb = {"NORMAL": (0, 65535, 0), "INPUT": (0, 0, 65535),
           "OUTPUT": (65535, 65535, 0)}[c["func"]]
    out = ["[TYPE:QCADCell]", "[TYPE:QCADDesignObject]",
           f"x={x:.6f}", f"y={y:.6f}", "bSelected=FALSE",
           f"clr.red={rgb[0]}", f"clr.green={rgb[1]}", f"clr.blue={rgb[2]}",
           f"bounding_box.xWorld={x - 9:.6f}", f"bounding_box.yWorld={y - 9:.6f}",
           "bounding_box.cxWorld=18.000000", "bounding_box.cyWorld=18.000000",
           "[#TYPE:QCADDesignObject]",
           "cell_options.cxCell=18.000000", "cell_options.cyCell=18.000000",
           "cell_options.dot_diameter=5.000000",
           f"cell_options.clock={c['clock']}",
           "cell_options.mode=QCAD_CELL_MODE_NORMAL",
           "cell_options.ignore_energy=FALSE",
           f"cell_function=QCAD_CELL_{c['func']}", "number_of_dots=4"]
    for dx, dy in ((4.5, -4.5), (4.5, 4.5), (-4.5, 4.5), (-4.5, -4.5)):
        out += ["[TYPE:CELL_DOT]", f"x={x + dx:.6f}", f"y={y + dy:.6f}",
                "diameter=5.000000", f"charge={QHALF:e}", "spin=0.000000",
                "potential=0.000000", "[#TYPE:CELL_DOT]"]
    if c["label"]:
        lx, ly = x, y - 20
        out += ["[TYPE:QCADLabel]", "[TYPE:QCADStretchyObject]",
                "[TYPE:QCADDesignObject]", f"x={lx:.6f}", f"y={ly:.6f}",
                "bSelected=FALSE", f"clr.red={rgb[0]}", f"clr.green={rgb[1]}",
                f"clr.blue={rgb[2]}", f"bounding_box.xWorld={lx - 10:.6f}",
                f"bounding_box.yWorld={ly - 11.5:.6f}",
                "bounding_box.cxWorld=20.000000", "bounding_box.cyWorld=23.000000",
                "[#TYPE:QCADDesignObject]", "[#TYPE:QCADStretchyObject]",
                f"psz={c['label']}", "[#TYPE:QCADLabel]"]
    out.append("[#TYPE:QCADCell]")
    return "\n".join(out)


def write_qca(path, cells):
    head = """[VERSION]
qcadesigner_version=2.000000
[#VERSION]
[TYPE:DESIGN]
[TYPE:QCADLayer]
type=3
status=1
pszDescription=Drawing Layer
[#TYPE:QCADLayer]
[TYPE:QCADLayer]
type=0
status=1
pszDescription=Substrate
[TYPE:QCADSubstrate]
[TYPE:QCADStretchyObject]
[TYPE:QCADDesignObject]
x=3000.000000
y=1500.000000
bSelected=FALSE
clr.red=65535
clr.green=65535
clr.blue=65535
bounding_box.xWorld=0.000000
bounding_box.yWorld=0.000000
bounding_box.cxWorld=6000.000000
bounding_box.cyWorld=3000.000000
[#TYPE:QCADDesignObject]
[#TYPE:QCADStretchyObject]
grid_spacing=20.000000
[#TYPE:QCADSubstrate]
[#TYPE:QCADLayer]
[TYPE:QCADLayer]
type=1
status=0
pszDescription=Main Cell Layer"""
    pos = [(c["col"], c["row"]) for c in cells]
    assert len(pos) == len(set(pos)), f"overlapping cells in {path}"
    with open(path, "w") as f:
        f.write(head + "\n")
        f.write("\n".join(cell_text(c) for c in cells) + "\n")
        f.write("[#TYPE:QCADLayer]\n[#TYPE:DESIGN]\n")


# ------------------------------------------------------------ layouts
def fa_cells(dc=0, dr=0, a="A", b="B", c="C", s="SUM", cy="CARRY",
             c_is_input=True, carry_out=True):
    """Fig 5b. Origin (0,0) = A cell; B at (2,-2)."""
    P = lambda col, row: (col + dc, row + dr)
    L = [cell(*P(2, -2), 0, "INPUT", b),
         cell(*P(1, -1), 0), cell(*P(2, -1), 1), cell(*P(3, -1), 0),
         cell(*P(0, 0), 0, "INPUT", a),
         cell(*P(1, 0), 1), cell(*P(2, 0), 1), cell(*P(3, 0), 1),
         cell(*P(3, 1), 1, "OUTPUT", s)]
    L.append(cell(*P(4, 0), 0, "INPUT" if c_is_input else "NORMAL",
                  c if c_is_input else None))
    if carry_out:
        L.append(cell(*P(5, 0), 1, "OUTPUT", cy))
    return L


def fs_cells():
    """Fig 6b: B.out above B, no cell right of C."""
    return [cell(2, -3, 1, "OUTPUT", "BOUT"),
            cell(2, -2, 0, "INPUT", "B"),
            cell(1, -1, 0), cell(2, -1, 1), cell(3, -1, 0),
            cell(0, 0, 0, "INPUT", "A"),
            cell(1, 0, 1), cell(2, 0, 1), cell(3, 0, 1),
            cell(4, 0, 0, "INPUT", "C"),
            cell(3, 1, 1, "OUTPUT", "DIFF")]


def fas_cells():
    """Fig 7b: FS + CARRY cell right of C."""
    L = fs_cells()
    L = [c for c in L if c["label"] != "DIFF"]
    L += [cell(3, 1, 1, "OUTPUT", "SUMDIFF"), cell(5, 0, 1, "OUTPUT", "CARRY")]
    return L


def rca_cells():
    """Fig 9, 64 cells. Stage i core starts at A_i = (2i, 2+5i)."""
    L = []
    for i in range(4):
        ac, ar = 2 * i, 2 + 5 * i
        L += [cell(ac + 2, ar - 2, 0, "INPUT", f"B{i}"),
              cell(ac + 1, ar - 1, 0), cell(ac + 2, ar - 1, 1), cell(ac + 3, ar - 1, 0),
              cell(ac, ar, 0, "INPUT", f"A{i}"),
              cell(ac + 1, ar, 1), cell(ac + 2, ar, 1), cell(ac + 3, ar, 1),
              cell(ac + 3, ar + 1, 1, "OUTPUT", f"S{i}")]
        if i == 0:
            # Cin input, then purple + 2 blue along the row
            L += [cell(4, 2, 0, "INPUT", "Cin"), cell(5, 2, 1),
                  cell(6, 2, 2), cell(7, 2, 2)]
            L += [cell(7, r, 3) for r in (3, 4, 5, 6)]           # 4 white
        else:
            # C_i tap (green), corner (green), 2 purple
            L += [cell(ac + 4, ar, 0), cell(ac + 5, ar, 0),
                  cell(ac + 6, ar, 1)]
            if i < 3:
                L += [cell(ac + 7, ar, 1),
                      cell(ac + 7, ar + 1, 2), cell(ac + 7, ar + 2, 2),
                      cell(ac + 7, ar + 3, 3), cell(ac + 7, ar + 4, 3)]
            else:
                L.append(cell(ac + 7, ar, 1, "OUTPUT", "COUT"))
    return L


if __name__ == "__main__":
    os.makedirs("qca", exist_ok=True)
    designs = {"approx_FA": fa_cells(), "approx_FS": fs_cells(),
               "approx_FAS": fas_cells(), "approx_RCA4": rca_cells()}
    for name, cells in designs.items():
        write_qca(f"qca/{name}.qca", cells)
        print(f"{name}: {len(cells)} cells")
