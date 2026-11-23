# Approximate Adder/Subtractor Circuits in QCA: Replication and Image-Blending Evaluation

VLSI course project, IIIT Sri City. Mukunth Parthasarathy (S20240010235).
Base paper: Seyedi & Abdoli, PLoS ONE 19(9): e0310050, 2024.

## What is here

| Folder | Contents |
|---|---|
| `layouts/` | QCADesigner `.qca` files: approximate FA (11 cells), FS (11), FA/S (12), 4-bit RCA (64), rebuilt from the paper's Figs 5b, 6b, 7b, 9. `test_FA_carry_via_wire.qca` = FA whose C arrives through clocked wire cells (shows why RCA stages 1-3 fail). Open any of them in QCADesigner-E. |
| `simulator/` | `qca_run.c`: headless runner for the QCADesigner-E engines (bistable, coherence vector + energy), exhaustive or vector-table input. `build.sh` builds it from the official QCADesigner-E source. Python decoders that turn traces into truth tables. `make_qca.py` writes the layouts. Vector files for the RCA (all 512 inputs, each held 4 clock cycles). |
| `analysis/` | `error_metrics.py` (ER, MED, NMED, MRED for the RCA), `image_blending.py` (blending at alpha = 0.2/0.5/0.8, 4-bit QCA RCA and 8-bit hybrid adder). |
| `data/` | Simulated RCA truth table (512 rows), raw 1-bit traces (bistable and coherence vector), energy logs. |
| `results/` | Result tables (t1-t8 CSV) and figures. |

## Reproduce

```sh
cd simulator && ./build.sh                       # builds qca_run
./qca_run ../layouts/approx_FA.qca BISTABLE bistable_paper_table2.opt fa.csv          # exhaustive, bistable
./qca_run ../layouts/approx_FA.qca CVE "T=2" fa_cv.csv                                 # coherence vector, prints Sum_Ebath
./qca_run ../layouts/approx_RCA4.qca BISTABLE bistable_paper_table2.opt rca.csv vec_rca_all.txt   # needs number_of_samples=409600
python check_rca.py rca.csv vec_rca_all.txt      # compares with SUM_i = A_i^B_i^Cin, CARRY = Cin
cd .. && pip install -r requirements.txt
python analysis/error_metrics.py
python analysis/image_blending.py
```

## Main results

- 1-bit FA, FS, FA/S: match the paper in all 8 cases (SUM/DIFF exact; CARRY = C and B.out = B, 25% error).
- 4-bit RCA (Fig 9 layout): stages 1-3 compute MAJ(A, NOT B, Cin) instead of XOR; ER 90.62% vs paper's 68.36%.
- Image blending (4-bit, alpha = 0.5): 9-13 dB PSNR. Hybrid 8-bit adder with 2 approximate LSBs: about 40 dB.

Simulation results only; no fabricated device was measured.

## Related files

Report and slides were submitted separately for the VLSI course review (23 Nov 2026). Paper figures used in the report are from Seyedi & Abdoli (2024), CC BY 4.0.
