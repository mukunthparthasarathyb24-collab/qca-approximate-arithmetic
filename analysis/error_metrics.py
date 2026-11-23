"""ER, MED, NMED, MRED, worst case for the 4-bit RCA: paper equations vs simulated layout (all 512 inputs)."""
import csv, os, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = list(csv.DictReader(open(os.path.join(ROOT, 'data', 'rca_simulated_truth_table.csv'))))
def metrics(key):
    ex = np.array([int(r['exact_A+B+Cin']) for r in rows]); ap = np.array([int(r[key]) for r in rows])
    ed = np.abs(ex - ap); nz = ex > 0
    return dict(ER=100 * np.mean(ed > 0), Cout_ER=100 * np.mean((ex >> 4) != (ap >> 4)), MED=ed.mean(),
                NMED=100 * ed.mean() / 31, MRED=100 * np.mean(ed[nz] / ex[nz]), worst=int(ed.max()))
for k in ('paper_model', 'simulated'):
    print(k, {a: round(float(b), 2) for a, b in metrics(k).items()})
