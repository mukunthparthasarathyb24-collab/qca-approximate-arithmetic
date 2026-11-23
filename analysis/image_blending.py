"""Image blending with the approximate QCA adder (method of Mendez et al., Electronics 2022).
P = (1-a)*S + a*T; weights exact, the addition done by the approximate adder.
Uses data/rca_simulated_truth_table.csv (QCADesigner-E bistable, all 512 inputs).
Run:  python analysis/image_blending.py      (needs numpy, scikit-image, matplotlib)"""
import csv, os, numpy as np
from skimage import data
from skimage.metrics import structural_similarity as ssim
from skimage.transform import resize
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
LUT = np.zeros((16, 16), dtype=np.int64)
for r in csv.DictReader(open(os.path.join(ROOT, 'data', 'rca_simulated_truth_table.csv'))):
    if r['Cin'] == '0': LUT[int(r['A']), int(r['B'])] = int(r['simulated'])
IDEAL = np.array([[a ^ b for b in range(16)] for a in range(16)])  # paper equations, Cin = 0

def hybrid8(A, B, k):
    """8-bit adder: k approximate LSB stages (behaviour seen in simulation), exact upper stages."""
    out = np.zeros_like(A); c = np.zeros_like(A)
    for i in range(8):
        a, b = (A >> i) & 1, (B >> i) & 1
        if i < k:
            s = a ^ b ^ c if i == 0 else ((a + (1 - b) + c) >= 2).astype(np.int64)
        else:
            s = a ^ b ^ c; c = (a & b) | (a & c) | (b & c)
        out |= s << i
    return out | (c << 8)

def norm(x):
    x = x if x.ndim == 2 else x[..., :3].mean(axis=2)
    x = resize(x, (256, 256), anti_aliasing=True); return (x - x.min()) / (x.max() - x.min())
yy, xx = np.mgrid[0:256, 0:256] / 255
pairs = {'moon+coins': (norm(data.moon()), norm(data.coins())),
         'brick+gravel': (norm(data.brick()), norm(data.gravel())),
         'gradient+blob': (xx, np.exp(-((xx - .5) ** 2 + (yy - .5) ** 2) / .05))}
def psnr(ref, img, peak):
    mse = np.mean((ref.astype(float) - img) ** 2); return float('inf') if mse == 0 else 10 * np.log10(peak ** 2 / mse)
print('images, alpha, adder, PSNR dB, SSIM')
for name, (S, T) in pairs.items():
    for a in (0.2, 0.5, 0.8):
        s4, t4 = np.round((1 - a) * S * 15).astype(int), np.round(a * T * 15).astype(int)
        for label, out in (('QCA RCA paper eq.', IDEAL[s4, t4]), ('QCA RCA simulated', LUT[s4, t4])):
            print(name, a, label, round(psnr(s4 + t4, out, 15), 2), round(ssim((s4 + t4).astype(float), out.astype(float), data_range=15), 3))
        s8, t8 = np.round((1 - a) * S * 255).astype(int), np.round(a * T * 255).astype(int)
        for k in (1, 2, 3, 4, 6, 8):
            out = hybrid8(s8, t8, k)
            print(name, a, f'hybrid k={k}', round(psnr(s8 + t8, out, 255), 2), round(ssim((s8 + t8).astype(float), out.astype(float), data_range=255), 3))
