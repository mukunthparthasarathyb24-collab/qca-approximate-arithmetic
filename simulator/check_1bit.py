"""Read the 1-bit simulation traces and print truth tables vs exact/paper logic."""
import sys
from decode import load, input_vectors, output_bits, align

maj = lambda a, b, c: int(a + b + c >= 2)
exact = {"SUM": lambda a, b, c: a ^ b ^ c, "DIFF": lambda a, b, c: a ^ b ^ c,
         "SUMDIFF": lambda a, b, c: a ^ b ^ c,
         "CARRY": maj, "BOUT": lambda a, b, c: maj(1 - a, b, c)}
paper = {"SUM": lambda a, b, c: a ^ b ^ c, "DIFF": lambda a, b, c: a ^ b ^ c,
         "SUMDIFF": lambda a, b, c: a ^ b ^ c,
         "CARRY": lambda a, b, c: c, "BOUT": lambda a, b, c: b}


def check(path, outputs, period=800, latency=0):
    d = load(path)
    vecs = input_vectors(d, ["A", "B", "C"], period)
    tables = {o: align(vecs, output_bits(d, o, 1, period), latency) for o in outputs}
    rows = {}
    for k, v in enumerate(vecs):
        key = (v["A"], v["B"], v["C"])
        if all(k in tables[o] for o in outputs):
            rows.setdefault(key, []).append({o: tables[o][k] for o in outputs})
    result = []
    for key in sorted(rows):
        a, b, c = key
        samples = rows[key]
        r = {"A": a, "B": b, "C": c}
        for o in outputs:
            bits = {s[o][0] for s in samples}
            pol = min(abs(s[o][1]) for s in samples)
            r[o] = bits.pop() if len(bits) == 1 else "X"
            r[o + "_pol"] = pol
            r[o + "_exact"] = exact[o](a, b, c)
            r[o + "_paper"] = paper[o](a, b, c)
        result.append(r)
    return result


if __name__ == "__main__":
    path, outs = sys.argv[1], sys.argv[2].split(",")
    for r in check(path, outs):
        print(r)
