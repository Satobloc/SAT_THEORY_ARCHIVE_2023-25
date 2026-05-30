
SAT K-map Pipeline — How to Use
===============================

1) Choose a *single* dynamical family (prefer non-molecular compact exotics).
2) Enter the masses (MeV) for that family in chronological order of complexity.
3) Propose one or more K-maps (integer lists), starting with a one-generator K that steps by +1.
4) Run evaluate_generators(masses, [K1, K2, ...], names) to score models by R^2, AIC/BIC, and a one-ahead prediction.
5) Prefer the simplest K-map (fewest generators) that achieves strong linearity and good holdout prediction.
6) Once fixed, freeze the K-map, quote sigma, and predict the next mass from pred_next_mass.
7) Cross-check with SAT's reconnection ordering (k_min increasing with perceived linkage).

You can modify 'demo_masses', 'K_G1', 'K_G2' directly in the notebook and re-run.
