"""Decode 4-bit RCA vector-table simulations (each vector held R clock cycles)."""
import sys
import numpy as np
from decode import load, output_bits

IN = ['A0', 'A1', 'A2', 'A3', 'B0', 'B1', 'B2', 'B3', 'Cin']
OUT = ['S0', 'S1', 'S2', 'S3', 'COUT']


def model(a, b, c):
    s = 0
    for i in range(4):
        s |= (((a >> i) & 1) ^ ((b >> i) & 1) ^ c) << i
    return s | (c << 4)


def decode_rca(path, vec_path, R=4, clk_out=1):
    d = load(path)
    lines = open(vec_path).read().split('\n')[1:]
    vecs = [list(map(int, l.split())) for l in lines if l.strip()]
    nslots = len(vecs)
    period = len(d['sample']) / nslots
    bits = {o: {s: (b, p) for s, b, p in output_bits(d, o, clk_out, period)} for o in OUT}
    groups = nslots // R
    rows = []
    for g in range(groups):
        v = vecs[g * R]
        a = sum(v[i] << i for i in range(4))
        b = sum(v[4 + i] << i for i in range(4))
        c = v[8]
        slot = g * R + R - 1                     # last cycle of the held vector
        out, pols = 0, []
        ok = True
        for i, o in enumerate(OUT):
            if slot not in bits[o]:
                ok = False
                break
            bit, pol = bits[o][slot]
            out |= bit << i
            pols.append(abs(pol))
        if ok:
            rows.append(dict(A=a, B=b, Cin=c, sim=out, model=model(a, b, c),
                             exact=a + b + c, min_pol=min(pols)))
    return rows


if __name__ == '__main__':
    rows = decode_rca(sys.argv[1], sys.argv[2])
    match = sum(r['sim'] == r['model'] for r in rows)
    print(f'{match}/{len(rows)} vectors match model (SUM_i = A_i^B_i^Cin, COUT = Cin)')
    for r in rows[:20]:
        print(r)
