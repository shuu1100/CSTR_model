# Phase 8 — Coverage, Data Quality, and Leakage Verification Report

- **Date:** 2026-10-13
- **Framework:** Mechanistic SciPy IVP + QMC Latin Hypercube Sampling

## 1. Disjoint Split & Leakage Verification

| Task | Split Method | Total IDs | Train | Val | Test | Overlap Count | Disjoint Assertion |
|---|---|---|---|---|---|---|---|
| Steady-State Regression | By Parameter Draw | 457 | 320 | 69 | 68 | 0 | **PASS** |
| Transient Dynamic Forecasting | By Trajectory ID | 127 | 89 | 19 | 19 | 0 | **PASS** |
| Kinetic Estimation Benchmark | By Trajectory ID | 30 | 21 | 4 | 5 | 0 | **PASS** |
| Fault Diagnosis & Anomaly | By Trajectory ID | 40 | 28 | 6 | 6 | 0 | **PASS** |

### Leakage Prevention Guarantees
1. **No Row-Level Splitting:** Consecutive timestamps from the same simulation trajectory are never scattered across splits.
2. **Locked Test Partition:** Test trajectory IDs are saved to `splits_manifest.json` and must remain strictly locked during model development and hyperparameter tuning.
3. **Train-Only Preprocessing:** Scalers, normalizers, and dimensionality reduction tools must be fit only on the train partition.

## 2. Statistical Distributions & Coverage

### Steady-State Dataset Statistics
```
            order         V_L     Q_L_min           k  C_A_in_mol_L     tau_min   damkohler  C_A_ss_mol_L  conversion  reaction_rate_ss      residual
count  457.000000  457.000000  457.000000  457.000000    457.000000  457.000000  457.000000    457.000000  456.000000        457.000000  4.570000e+02
mean     1.000000   25.346609    2.534215    0.535572      2.547849   21.372692   11.769071      0.902689    0.659909         -0.225995  5.193312e-03
std      0.813806   14.184120    1.416657    0.525870      1.419127   39.568185   35.445307      1.050568    0.303376          0.409074  2.062415e-02
min      0.000000    1.061785    0.103053    0.005842      0.000000    0.341007    0.005000      0.000000    0.003833         -4.157327 -9.992007e-16
25%      0.000000   12.988295    1.304243    0.118782      1.319821    5.141828    0.860709      0.178059    0.454387         -0.253256 -3.469447e-18
50%      1.000000   25.194919    2.524980    0.331251      2.526702   10.136980    3.262187      0.488377    0.762319         -0.115839  0.000000e+00
75%      2.000000   37.679640    3.760783    0.828805      3.778058   18.280885   10.400834      1.181964    0.919883         -0.031607  2.775558e-17
max      2.000000   49.996533    4.974230    1.990803      5.000000  355.618057  514.554525      4.362340    1.000000          0.000000  1.435825e-01
```

### Transient Trajectories Statistics
```
           time_min  C_A_clean_mol_L  C_A_noisy_mol_L  reaction_rate_mol_L_min
count  12827.000000     12827.000000     12827.000000             12827.000000
mean      30.964519         0.974208         0.974703                -0.268832
std       27.191045         1.043818         1.043399                 0.576506
min        0.000000         0.000000         0.000000               -16.586934
25%       11.000000         0.162100         0.166883                -0.239527
50%       22.212319         0.577504         0.575929                -0.119796
75%       43.888510         1.415876         1.421786                -0.049787
max      120.000000         4.992672         5.018843                -0.000000
```

### Fault Diagnosis Statistics
```
          time_min  C_A_measured_mol_L  C_A_true_mol_L      Q_L_min     severity
count  2040.000000         2040.000000     2040.000000  2040.000000  2040.000000
mean     28.670923            0.809824        0.800677     1.342490     0.536747
std      26.519110            0.525846        0.519793     0.569948     0.406778
min       0.000000            0.038187        0.074738     0.118148     0.000000
25%      10.306081            0.421806        0.395537     0.911148     0.233467
50%      21.011519            0.676929        0.656426     1.377285     0.524891
75%      37.941129            0.983753        0.979067     1.763139     0.765765
max     152.261183            3.178718        3.167968     2.332120     1.493115
```

## 3. Physical Plausibility Checks

- Minimum concentration across all dynamic points: `0.000000 mol/L` (strictly non-negative: **PASS**)
- Minimum noisy concentration after clipping: `0.000000 mol/L` (strictly non-negative: **PASS**)
- Number of NaN values in primary concentration: `0` (**PASS**)
- Reaction orders covered: Orders 0, 1, 2 evenly represented across LHS sweeps.
