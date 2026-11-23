"""Decode vector-table runs where each vector is held R cycles; read last cycle."""
import sys
from decode import load, output_bits

def decode_held(path, vec_path, outs, R=4, clk=1):
    d = load(path)
    lines = [l for l in open(vec_path).read().split('\n')]
    names = lines[0].split()
    vecs = [list(map(int, l.split())) for l in lines[1:] if l.strip()]
    period = len(d['sample']) / len(vecs)
    bits = {o: {s: (b, p) for s, b, p in output_bits(d, o, clk, period)} for o in outs}
    rows = []
    for g in range(len(vecs) // R):
        v = dict(zip(names, vecs[g * R]))
        slot = g * R + R - 1
        r = dict(v)
        for o in outs:
            b, p = bits[o].get(slot, (None, 0.0))
            r[o] = b; r[o + '_pol'] = abs(p)
        rows.append(r)
    return rows

if __name__ == '__main__':
    for r in decode_held(sys.argv[1], sys.argv[2], sys.argv[3].split(',')):
        print(r)
