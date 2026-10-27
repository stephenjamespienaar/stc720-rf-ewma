# SPY variance-targeting review (training data only)

Snapshot `7cd6d400b798c5e7…`; 3507 training returns 1993-02-01 to 2006-12-29; mean 0.04029%, s² 1.1443.

| Quantity | A: unrestricted ML (arch) | A': unrestricted ML, project likelihood (h1 = s2) | B: variance-targeted ML |
|---|---|---|---|
| ω | 0.00457 | 0.00477 | 0.00513 |
| α | 0.0599 | 0.0617 | 0.0593 |
| β | 0.9377 | 0.9358 | 0.9363 |
| ν | 7.35 | 7.36 | 7.63 |
| α + β | 0.9976 | 0.9975 | 0.9955 |
| Implied unconditional variance | 1.920 | 1.904 | 1.144 |
| Training s² | 1.144 | 1.144 | 1.144 |
| Implied / s² | 1.678 | 1.664 | 1.000 |
| Fourth-moment coefficient β²+2αβ+κα² | 1.0089 | 1.0094 | 1.0039 |
| κ = E η⁴ | 4.793 | 4.784 | 4.652 |
| Finite variance | yes | yes | yes |
| Finite fourth moment | no | no | no |
| Strict simulator gate (ν > 4, m4 ≤ 0.99) | no | no | no |
| Half-life (days) | 291 | 276 | 154 |
| Log-likelihood, project convention (h₁ = s²) | -4626.61 | -4626.59 | -4626.83 |
| Log-likelihood, arch (backcast) | -4625.72 | – | – |
| Training mean ĥ | 1.178 | 1.178 | 1.148 |
| Training mean u = r²/ĥ | 0.993 | 0.995 | 1.014 |
| Training median u | 0.340 | 0.340 | 0.345 |
| Training QLIKE (proxy r²) | 0.8344 | 0.8343 | 0.8344 |
| Training ACF₁ of u | -0.007 | -0.008 | -0.007 |
| Excess kurtosis of r/√ĥ | 1.57 | 1.57 | 1.57 |
| Min / max ĥ | 0.211 / 6.764 | 0.210 / 6.866 | 0.212 / 6.627 |
| ĥ on 2006-12-29 | 0.277 | 0.277 | 0.277 |

Twice the log-likelihood difference A′ − B (same likelihood and start): 0.47 (descriptive; s² is estimated, so a χ²₁ reference is only approximate).
corr(ĥ_A, ĥ_B) over training = 1.0000; mean ĥ_A/ĥ_B = 1.021.
Sub-period mean r²: 1993-02-01–1999-12-31 0.951, 2000-01-01–2003-12-31 2.013, 2004-01-01–2006-12-29 0.436.

Optimizer, B: {"convergence_flag": 0, "message": "Optimization terminated successfully.", "nit": 24, "grad_norm": 1.645887049613485e-07, "n_starts": 12, "n_converged": 12, "n_at_best": 12, "max_param_spread_at_best": 0.0004843893275694455, "objective_range_converged": 2.0146095391915253e-07}
Optimizer, A′: {"success": true, "message": "Optimization terminated successfully.", "nit": 34, "grad_norm": 6.322027276634104e-08}
Optimizer, A (arch): {"convergence_flag": 0, "loglik": -4625.7154580417155, "near_boundary": true}

Checks: {"training prices end 2006-12-29": true, "n_train equals stopped run (3507)": true, "training mean equals stopped run": true, "s2 equals stopped run": true, "unrestricted fit reproduces the stopped run exactly": true, "B targets s2 exactly": true, "B optimum agrees across starts": true}
