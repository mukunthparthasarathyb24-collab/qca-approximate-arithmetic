"""Decode QCADesigner-E trace CSVs (from qca_run) into per-vector logic values."""
import csv
import numpy as np


def load(path):
    rows = list(csv.DictReader(open(path)))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def hold_windows(clk, frac=0.25):
    """Contiguous sample ranges where this clock is in its low (hold) part."""
    lo, hi = clk.min(), clk.max()
    m = clk < lo + frac * (hi - lo)
    edges = np.diff(m.astype(int))
    starts = list(np.nonzero(edges == 1)[0] + 1)
    ends = list(np.nonzero(edges == -1)[0] + 1)
    if m[0]:
        starts = [0] + starts
    if m[-1]:
        ends = ends + [len(m)]
    return list(zip(starts, ends))


def input_vectors(d, inputs, period):
    n = int(len(d["sample"]) // period)
    vecs = []
    for k in range(n):
        a, b = int(k * period), int((k + 1) * period)
        vecs.append({i: int(d["in:" + i][a:b].sum() > 0) for i in inputs})
    return vecs


def output_bits(d, out, clk_zone, period):
    """Returns list of (vector_slot, bit, polarisation) for each hold window."""
    res = []
    for a, b in hold_windows(d["clk%d" % clk_zone]):
        if b - a < 3:
            continue
        p = d["out:" + out][a:b]
        pol = p[len(p) // 2]                  # middle of the hold plateau
        slot = int(((a + b) // 2) // period)
        res.append((slot, int(pol > 0), pol))
    return res


def align(vecs, obits, latency):
    """Map hold windows to input vectors assuming `latency` clock periods."""
    table = {}
    for slot, bit, pol in obits:
        k = slot - latency
        if 0 <= k < len(vecs):
            table[k] = (bit, pol)
    return table
