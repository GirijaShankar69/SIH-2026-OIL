# Digital Twin Assumptions & Known Limitations

## 1. Subsurface Physics Assumptions
- **Homogeneity**: Pay zone is assumed to have uniform permeability ($280\text{ mD}$) and porosity ($0.24$) in radial coordinates around the wellbore.
- **Thermal Front**: Marx-Langenheim cylindrical steam chamber approximation assumes uniform radial heat growth without localized fracture channeling.
- **PVT Fluid Calibration**: Oil viscosity is modeled via calibrated Andrade-Walther equations fitted to Baghewala 18.2° API dead crude.

---

## 2. Artificial Lift & Dynamics Assumptions
- **Wave Propagation**: Sucker rod dynamics are modeled using 1D damped wave equation (Gibbs method) along the tapered rod string.
- **Damping**: Hydrodynamic viscous damping is computed from annular shear stresses assuming concentric rod travel inside the tubing string.

---

## 3. Data & Validation Limitations
- **Synthetic Benchmark Validation**: Real-time continuous streaming from OIL SCADA RTUs is simulated using calibrated physical parameters. All validation figures reflect synthetic physics benchmark performance until live field streaming is active.
- **Economic Objective**: Financial comparisons are evaluated using a **Net Profit Proxy** (Revenue minus steam generation OPEX and electrical lifting cost) rather than a discounted multi-year DCF/NPV cash-flow model.
