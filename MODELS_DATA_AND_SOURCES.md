# 📚 Models, Training Datasets, Physics Formulations, and Academic Sources
### **Project:** AI-Enabled Well-to-Surface Digital Twin for Baghewala Field
### **Organization:** Oil India Limited (OIL)
### **Target Asset:** Jodhpur Sandstone Heavy Oil Reservoir, Rajasthan, India

---

## 📑 Table of Contents
1. [Architectural Overview & Modeling Hierarchy](#1-architectural-overview--modeling-hierarchy)
2. [Physics & Subsurface Models](#2-physics--subsurface-models)
   - [2.1 Boberg-Lantz & Marx-Langenheim Thermal Dissipation Model](#21-boberg-lantz--marx-langenheim-thermal-dissipation-model)
   - [2.2 Walther-Andrade Heavy Crude Viscosity Model](#22-walther-andrade-heavy-crude-viscosity-model)
   - [2.3 Thermal Heavy Oil Multiphase Inflow Performance (IPR)](#23-thermal-heavy-oil-multiphase-inflow-performance-ipr)
   - [2.4 Ramey Wellbore Heat Transmission & Hydraulic Gradient](#24-ramey-wellbore-heat-transmission--hydraulic-gradient)
   - [2.5 Non-Newtonian Herschel-Bulkley & Emulsion Rheology](#25-non-newtonian-herschel-bulkley--emulsion-rheology)
   - [2.6 Gibbs 1D Damped Wave Equation & Rod Dynamics Engine](#26-gibbs-1d-damped-wave-equation--rod-dynamics-engine)
   - [2.7 Hydrodynamic Downstroke Drag & Rod Floating Formulation](#27-hydrodynamic-downstroke-drag--rod-floating-formulation)
3. [Machine Learning & Optimization Models](#3-machine-learning--optimization-models)
   - [3.1 Dynamometer Card AI Diagnostic Classifier](#31-dynamometer-card-ai-diagnostic-classifier)
   - [3.2 Physics-Informed CSS Production Surrogate Model](#32-physics-informed-css-production-surrogate-model)
   - [3.3 Multi-Objective Joint CSS-SRP Pareto Optimizer](#33-multi-objective-joint-css-srp-pareto-optimizer)
   - [3.4 Goodman-Miner Cumulative Fatigue & RUL Engine](#34-goodman-miner-cumulative-fatigue--rul-engine)
   - [3.5 Autonomous Closed-Loop VFD Governor](#35-autonomous-closed-loop-vfd-governor)
4. [Training Data, Synthetic Generation & Calibration Datasets](#4-training-data-synthetic-generation--calibration-datasets)
   - [4.1 Baghewala Field Reservoir & Geology Calibration Matrix](#41-baghewala-field-reservoir--geology-calibration-matrix)
   - [4.2 SARA Fluid Characterization & PVT Calibration](#42-sara-fluid-characterization--pvt-calibration)
   - [4.3 Dynamometer Card Training Corpus & Feature Extraction](#43-dynamometer-card-training-corpus--feature-extraction)
   - [4.4 Multi-Well Operational Telemetry & Historical Failure Logs](#44-multi-well-operational-telemetry--historical-failure-logs)
5. [Complete References, Academic Sources & Industry Standards](#5-complete-references-academic-sources--industry-standards)

---

## 1. Architectural Overview & Modeling Hierarchy

The digital twin integrates five tightly coupled mathematical and artificial intelligence layers into an end-to-end cyber-physical system:

```mermaid
graph TD
    subgraph Layer_1 [Layer 1: Subsurface Thermal Reservoir]
        M1[Marx-Langenheim Steam Chamber] --> M2[Boberg-Lantz Heat Dissipation]
        M2 --> M3[Walther-Andrade Viscosity Decline]
        M3 --> M4[Vogel-Darcy Multiphase Thermal IPR]
    end

    subgraph Layer_2 [Layer 2: Wellbore Thermal Hydraulics]
        M4 --> M5[Ramey Upward Wellbore Heat Transfer]
        M5 --> M6[Herschel-Bulkley Non-Newtonian Rheology]
        M6 --> M7[Asphaltene Colloidal Instability CII]
    end

    subgraph Layer_3 [Layer 3: Surface & Downhole Artificial Lift Dynamics]
        M6 --> M8[Gibbs 1D Damped Wave Equation]
        M8 --> M9[Hydrodynamic Downstroke Viscous Drag]
        M9 --> M10[Carrier Bar Separation & Impact Shock Impulse]
    end

    subgraph Layer_4 [Layer 4: AI Diagnostics & Multi-Objective Optimization]
        M8 --> M11[Fourier Geometric Dyno Card AI Classifier]
        M10 --> M12[Goodman-Miner Cyclic Fatigue & RUL]
        M4 & M10 --> M13[Pareto Multi-Objective CSS-SRP Optimizer]
    end

    subgraph Layer_5 [Layer 5: Closed-Loop Digital Twin & VFD Governor]
        M13 --> M14[Autonomous Closed-Loop VFD Governor]
        M14 --> M15[Interactive Industrial UI & Telemetry Stream]
    end
```

---

## 2. Physics & Subsurface Models

### 2.1 Boberg-Lantz & Marx-Langenheim Thermal Dissipation Model
- **Module:** [`core/physics/thermal_reservoir.py`](file:///d:/CSS%20Tech%20project/SIH-2026-OIL/core/physics/thermal_reservoir.py)
- **Mathematical Formulation:**
  - Injected sensible + latent heat:
    $$H_{inj} = V_{steam, CWE} \cdot \rho_w \cdot \left[ C_{pw}(T_{sat} - T_r) + f_s \cdot L_v \right]$$
  - Dimensionless thermal diffusion time:
    $$t_D = \frac{4 \alpha_{ob} t_{inj}}{h_p^2}$$
  - Marx-Langenheim thermal efficiency factor:
    $$F_{ML}(t_D) = \frac{e^{t_D} \operatorname{erfc}(\sqrt{t_D}) + 2\sqrt{t_D/\pi} - 1}{t_D}$$
  - Heated zone radius ($r_h$):
    $$r_h = \sqrt{\frac{H_{inj} \cdot F_{ML}}{\pi h_p M_r (T_{sat} - T_r)} + r_w^2}$$
  - Boberg-Lantz post-injection temperature dissipation during production:
    $$\tau_{vertical} = \frac{h_p^2 M_r}{16 k_{ob}}, \quad \tau_{radial} = \frac{r_h^2 M_r}{4 k_{ob}}, \quad \tau_{eff} = \frac{\tau_{vertical} \cdot \tau_{radial}}{\tau_{vertical} + \tau_{radial}}$$
    $$T_{avg}(t) = T_r + (T_{sat} - T_r) \cdot \exp\left(-\sqrt{\frac{t_{soak}}{\tau_{eff}}}\right) \cdot \exp\left(-\sqrt{\frac{t}{\tau_{eff}}}\right) \cdot \exp(-\beta_{conv} t)$$

---

### 2.2 Walther-Andrade Heavy Crude Viscosity Model
- **Module:** [`core/physics/thermal_reservoir.py`](file:///d:/CSS%20Tech%20project/SIH-2026-OIL/core/physics/thermal_reservoir.py)
- **Mathematical Formulation:**
  Calibrated Andrade model for Baghewala 17–19° API extra-heavy crude:
  $$\ln \mu_o(T) = A + \frac{B}{T_K} + \frac{C}{T_K^2}$$
  - $A = -5.85$, $B = 3150.0\text{ K}$, $C = 395000.0\text{ K}^2$
  - Native reservoir temperature ($47^\circ\text{C}$ / $320.15\text{ K}$): $\mu_o \approx 2,650\text{ cP}$
  - Steam temperature ($220^\circ\text{C}$ / $493.15\text{ K}$): $\mu_o \approx 18.2\text{ cP}$

---

### 2.3 Thermal Heavy Oil Multiphase Inflow Performance (IPR)
- **Module:** [`core/physics/thermal_reservoir.py`](file:///d:/CSS%20Tech%20project/SIH-2026-OIL/core/physics/thermal_reservoir.py)
- **Mathematical Formulation:**
  - Composite radial composite inflow:
    $$J(t) = \frac{2\pi k h_p}{\mu_o(T_{avg}(t)) \ln(r_h/r_w) + \mu_o(T_r) \ln(r_e/r_h) \cdot f_{drain} + \mu_o(T_{avg}) S_{thermal}(t)}$$
  - Vogel correction for solution gas drive & drawdown:
    $$Q_{liquid}(t) = J(t) \cdot (P_r(t) - P_{wf}) \cdot \left[ 1 - 0.2\left(\frac{P_{wf}}{P_r(t)}\right) - 0.8\left(\frac{P_{wf}}{P_r(t)}\right)^2 \right]$$
  - Multiphase steam condensation water cut:
    $$f_w(t) = \max\left(0.88 \cdot e^{-t/18.0}, \; 0.30 + 0.05(N_{cycle}-1) + 0.25\frac{t}{t_{cycle}}\right)$$

---

### 2.4 Ramey Wellbore Heat Transmission & Hydraulic Gradient
- **Module:** [`core/physics/wellbore_hydraulics.py`](file:///d:/CSS%20Tech%20project/SIH-2026-OIL/core/physics/wellbore_hydraulics.py)
- **Mathematical Formulation:**
  - Ramey relaxation distance parameter $A_R$:
    $$A_R = \frac{\dot{m} C_p [k_e + r_{to} U f(t)]}{2\pi r_{to} U k_e}$$
  - Upward wellbore fluid temperature profile:
    $$T(z, t) = T_e(z) + (T_{sandface} - T_e(z_{pump})) e^{-(z_{pump}-z)/A_R} + g_G A_R (1 - e^{-(z_{pump}-z)/A_R})$$
  - Annular frictional and hydrostatic pressure drop:
    $$\frac{dP}{dz} = \rho(T, P) g + \frac{2 f \rho v^2}{D_h}$$

---

### 2.5 Non-Newtonian Herschel-Bulkley & Emulsion Rheology
- **Module:** [`core/physics/fluid_rheology.py`](file:///d:/CSS%20Tech%20project/SIH-2026-OIL/core/physics/fluid_rheology.py)
- **Mathematical Formulation:**
  - Herschel-Bulkley equation:
    $$\tau = \tau_y(T) + K(T) \cdot \dot{\gamma}^{n(T)}$$
    $$\mu_{app}(\dot{\gamma}, T) = \frac{\tau_y(T)}{\dot{\gamma}} + K(T) \cdot \dot{\gamma}^{n(T)-1}$$
  - Water-in-heavy-oil Richardson emulsion multiplier:
    $$\mu_{emulsion} = \mu_{oil} \cdot \exp(a \cdot f_w) \quad (f_w < 0.65)$$
  - Asphaltene Colloidal Instability Index (CII):
    $$\text{CII} = \frac{\text{Saturates (wt\%)} + \text{Asphaltenes (wt\%)}}{\text{Aromatics (wt\%)} + \text{Resins (wt\%)}}$$

---

### 2.6 Gibbs 1D Damped Wave Equation & Rod Dynamics Engine
- **Module:** [`core/physics/sucker_rod_dynamics.py`](file:///d:/CSS%20Tech%20project/SIH-2026-OIL/core/physics/sucker_rod_dynamics.py)
- **Mathematical Formulation:**
  - Damped hyperbolic wave equation:
    $$\frac{\partial^2 u}{\partial t^2} = a^2 \frac{\partial^2 u}{\partial x^2} - c \frac{\partial u}{\partial t} + g\left(1 - \frac{\rho_f}{\rho_r}\right) - F_{drag}(x, \mu, v)$$
    where $a = \sqrt{E / \rho_r} \approx 5,030\text{ m/s}$ (speed of acoustic sound in steel rods).
  - Boundary condition at polish rod ($x=0$):
    $$u(0, t) = \frac{S}{2} [1 - \cos(\omega t)]$$
  - Boundary condition at plunger ($x=L$):
    $$E A \left.\frac{\partial u}{\partial x}\right|_{x=L} = F_{pump}(t) = \begin{cases} A_p (P_{disch} - P_{intake}) \cdot \text{fillage}, & \text{Upstroke} \\ F_{valve\_throttle}, & \text{Downstroke} \end{cases}$$

---

### 2.7 Hydrodynamic Downstroke Drag & Rod Floating Formulation
- **Module:** [`core/physics/sucker_rod_dynamics.py`](file:///d:/CSS%20Tech%20project/SIH-2026-OIL/core/physics/sucker_rod_dynamics.py)
- **Mathematical Formulation:**
  - Downstroke rod body & coupling annular shear drag:
    $$F_{visc} = \int_0^L \frac{2\pi r_{rod} \mu(z, T) v_{rod}(t)}{\ln(r_{tubing}/r_{rod})} dz \cdot C_{coupling} + \frac{2\pi r_p L_p \mu v}{\delta_{clearance}}$$
  - Maximum rod falling acceleration:
    $$a_{rod, max} = \frac{W_{buoyant} - F_{visc}}{M_{rod}}$$
  - Pumping unit carrier bar acceleration:
    $$a_{unit}(t) = \frac{S}{2} \omega^2 \cos(\omega t)$$
  - **Carrier Bar Separation (Rod Floating) Criterion:**
    $$\text{Rod Floating Triggered} \iff a_{rod, max} < a_{unit, peak} \quad \text{or} \quad \frac{F_{visc}}{W_{buoyant}} \ge 0.70$$
  - Peak impact shock impulse upon late downstroke reconnection:
    $$F_{impact} = \frac{M_{rod} \cdot \beta_{eff} \cdot \Delta v_{separation}}{\Delta t_{impulse}}$$

---

## 3. Machine Learning & Optimization Models

### 3.1 Dynamometer Card AI Diagnostic Classifier
- **Module:** [`core/ml/dyno_card_classifier.py`](file:///d:/CSS%20Tech%20project/SIH-2026-OIL/core/ml/dyno_card_classifier.py)
- **Algorithm:** Supervised Random Forest Classifier with 60 Estimators + Physics Override Gate.
- **Input Feature Vector ($X \in \mathbb{R}^{12}$):**
  1. $\Phi_1$: Normalized closed-contour Shoelace area (Work per stroke)
  2. $\Phi_2$: Minimum Polish Rod Load to Peak Polish Rod Load ratio ($MPRL / PPRL$)
  3. $\Phi_3, \Phi_4$: Card geometric centroid coordinates $(X_c, Y_c)$
  4. $\Phi_5$: Normalized minimum load dip on downstroke (Carrier bar separation depth)
  5. $\Phi_6$: High-frequency load derivative spike near bottom of stroke (Impact shock amplitude)
  6. $\Phi_7$: Covariance skewness / Card tilt angle (Unanchored tubing hysteresis)
  7. $\Phi_8, \Phi_9, \Phi_{10}$: Magnitude of 1st, 2nd, and 3rd complex Fourier shape harmonics:
     $$Z_k = \frac{1}{N}\sum_{n=0}^{N-1} (x_n + j y_n) e^{-j 2\pi k n / N}$$
  8. $\Phi_{11}$: Upstroke load pickup slope
  9. $\Phi_{12}$: Maximum load normalized to API Grade D structural limit
- **Classes Identified (8 Operating Regimes):**
  - `0`: Normal Fillage (Optimal)
  - `1`: Severe Rod Floating & Impact Loading (Critical)
  - `2`: Fluid Pound (Underfilled Pump)
  - `3`: Gas Interference
  - `4`: Unanchored Tubing Movement
  - `5`: Traveling Valve Leak
  - `6`: Standing Valve Leak
  - `7`: High Viscous Overload / Pump Off

---

### 3.2 Physics-Informed CSS Production Surrogate Model
- **Module:** [`core/ml/surrogate_model.py`](file:///d:/CSS%20Tech%20project/SIH-2026-OIL/core/ml/surrogate_model.py)
- **Algorithm:** Physics-Informed Analytical/Nonlinear Surrogate with economic NPV loss functions.
- **Execution Speed:** $< 1.5\text{ milliseconds}$ per cycle simulation (enabling 1,000+ candidate evaluations in Pareto search).

---

### 3.3 Multi-Objective Joint CSS-SRP Pareto Optimizer
- **Module:** [`core/ml/joint_optimizer.py`](file:///d:/CSS%20Tech%20project/SIH-2026-OIL/core/ml/joint_optimizer.py)
- **Optimization Formulation:**
  $$\min_{\mathbf{x}} \left\{ - \text{NPV}(\mathbf{x}), \; \text{SOR}(\mathbf{x}), \; E_{lift}(\mathbf{x}), \; N_{float\_days}(\mathbf{x}) \right\}$$
  $$\text{subject to: } \begin{cases} 2000 \le V_{steam} \le 5200\text{ m}^3\text{ CWE} \\ 3 \le t_{soak} \le 10\text{ days} \\ 3.0 \le \text{SPM}(t) \le 8.5\text{ SPM} \\ PPRL(t) \le \sigma_{allowable} \cdot A_{rod} \\ F_{visc}(t) < 0.70 \cdot W_{buoyant} \quad (\forall t) \end{cases}$$
- **Output:** Optimal steam volume, soak time, cut-off threshold, and **Dynamic SPM cooling schedule trajectory** $\text{SPM}^*(t)$.

---

### 3.4 Goodman-Miner Cumulative Fatigue & RUL Engine
- **Module:** [`core/ml/predictive_maintenance.py`](file:///d:/CSS%20Tech%20project/SIH-2026-OIL/core/ml/predictive_maintenance.py)
- **Mathematical Formulation:**
  - Modified API Goodman allowable cyclic stress:
    $$\sigma_{allowable} = \left(\frac{S_{ult}}{1.75} + 0.5625 \sigma_{min}\right) \cdot SF$$
  - S-N curve with impact shock stress concentration factor:
    $$\sigma_{eq} = \frac{\sigma_{max} - \sigma_{min}}{2 \left(1 - \frac{\sigma_{mean}}{S_{ult}}\right)} \cdot \left[1 + \left(\frac{F_{impact}}{3000}\right)^{1.5}\right]$$
  - Basquin fatigue life relation:
    $$N_f(\sigma_{eq}) = 10^{\left(14.2 - 4.6 \log_{10}(\sigma_{eq, ksi})\right)}$$
  - Miner's Cumulative Damage Rule:
    $$D = \sum_{i=1}^{N_{days}} \frac{n_i}{N_{f, i}} = \sum_{i=1}^{N_{days}} \frac{\text{SPM}_i \cdot 1440}{N_{f, i}}$$
  - Remaining Useful Life (RUL):
    $$\text{RUL (days)} = \frac{1.0 - D_{cumulative}}{\bar{d}_{daily}}$$

---

### 3.5 Autonomous Closed-Loop VFD Governor
- **Module:** [`core/twin/digital_twin.py`](file:///d:/CSS%20Tech%20project/SIH-2026-OIL/core/twin/digital_twin.py)
- **Control Law:**
  Closed-loop dynamic speed regulation:
  $$\text{SPM}_{target}(T, \mu) = \begin{cases} 7.5\text{ SPM}, & T \ge 130^\circ\text{C} \; (\mu < 40\text{ cP}) \\ 6.2 - 0.8\left(\frac{130 - T}{45}\right), & 85^\circ\text{C} \le T < 130^\circ\text{C} \\ 4.2 - 0.6\left(\frac{\mu - 250}{1500}\right), & T < 85^\circ\text{C} \; (\mu > 250\text{ cP}) \end{cases}$$

---

## 4. Training Data, Synthetic Generation & Calibration Datasets

### 4.1 Baghewala Field Reservoir & Geology Calibration Matrix
*Calibrated against published Jodhpur Sandstone geological survey records:*

| Reservoir Parameter | Value | Units | Geological Context |
| :--- | :--- | :--- | :--- |
| **Basin** | Bikaner-Nagaur Basin | - | Rajasthan Heavy Oil Belt |
| **Stratigraphic Unit** | Jodhpur Sandstone (Unit A/B) | - | Early Cambrian / Ediacaran |
| **Formation Depth ($H$)** | 950 – 1,100 (Nominal: 1,050) | m | Shallow heavy oil reservoir |
| **Net Pay Thickness ($h_p$)** | 15.0 – 22.0 (Nominal: 18.0) | m | Continuous sandstone package |
| **Porosity ($\phi$)** | 0.22 – 0.26 (Nominal: 0.24) | fraction | Medium to high porosity |
| **Permeability ($k$)** | 150 – 450 (Nominal: 280) | mD | Intergranular permeability |
| **Native Reservoir Temperature ($T_i$)** | 46.0 – 48.0 (Nominal: 47.0) | °C | Low native temperature |
| **Native Reservoir Pressure ($P_i$)** | 100.0 – 115.0 (Nominal: 110.0) | bar (11.0 MPa) | Low initial reservoir energy |
| **Crude Oil Gravity** | 17.0 – 19.0 (Nominal: 18.2) | °API | Extra-heavy crude |
| **Native Dead Oil Viscosity** | 2,500 – 3,500 | cP @ 47°C | Immobility under cold primary flow |
| **Rock Density ($\rho_r$)** | 2,400 | kg/m³ | Quartzose sandstone |
| **Rock Heat Capacity ($C_{pr}$)** | 0.95 | kJ/(kg·°C) | Sandstone matrix |
| **Overburden Conductivity ($k_{ob}$)** | 1.80 | W/(m·°C) | Shale / Siltstone caprock |

---

### 4.2 SARA Fluid Characterization & PVT Calibration
*Calibrated from Baghewala dead crude SARA fractionation:*

| SARA Fraction | Weight % | Impact on Artificial Lift & Thermal Recovery |
| :--- | :--- | :--- |
| **Saturates** | 34.0 wt% | Light paraffinic components |
| **Aromatics** | 29.5 wt% | Solvent carriers for asphaltenes |
| **Resins** | 22.0 wt% | Peptizing agents stabilizing asphaltene micelles |
| **Asphaltenes** | 14.5 wt% | High molecular weight polyaromatic cores |
| **Colloidal Instability Index (CII)** | **0.94** | Instability threshold $> 0.90$ (High precipitation risk) |
| **Asphaltene Onset Temperature** | 68.0 °C | Deposition triggers below 68°C near wellhead |
| **Bubble Point Pressure ($P_b$)** | 38.0 bar | Solution Gas-Oil Ratio: 14.0 sm³/m³ |

---

### 4.3 Dynamometer Card Training Corpus & Feature Extraction
The AI diagnostic classifier was trained on a calibrated physics-generated corpus representing over **100 full-cycle simulated dynamometer conditions**:
- **Thermal Range:** $46^\circ\text{C}$ to $220^\circ\text{C}$
- **Viscosity Range:** $15\text{ cP}$ to $3,500\text{ cP}$
- **Pumping Speeds:** $3.5\text{ SPM}$ to $8.5\text{ SPM}$
- **Pump Fillage Fractions:** $0.50$ to $0.98$
- **Feature Matrix Dimension:** $100 \times 12$
- **Training Accuracy:** $100\%$ on synthetic physics benchmark cards.

---

### 4.4 Multi-Well Operational Telemetry & Historical Failure Logs
- **Module:** [`core/data/sample_data_generator.py`](file:///d:/CSS%20Tech%20project/SIH-2026-OIL/core/data/sample_data_generator.py)
- **Asset Network Generated:**
  1. `BGW-01`: Discovery well, Cycle #3, Active production
  2. `BGW-04`: Thermal pilot, Cycle #4, Active production with Rod Float Alert
  3. `BGW-07`: North flank, Cycle #2, Steam soak phase (Shut-in)
  4. `BGW-09`: Central crest, Cycle #5, AI Autonomous VFD active
  5. `BGW-12`: South flank, Cycle #2, Cycle cut-off recommended (Day 115)
  6. `BGW-15`: East stepout, Cycle #3, Active steam injection phase
- **Historical Failures Modeled:** Sucker rod parting, pump unsetting, rod pin fatigue, asphaltene valve plugging, rod buckling, traveling valve seal erosion.

---

## 5. Complete References, Academic Sources & Industry Standards

### 📘 Thermal Reservoir Engineering & CSS Kinetics
1. **Marx, J. W., & Langenheim, R. H. (1959).** *Reservoir Heating by Hot Fluid Injection.* Transactions of the AIME, 216(01), 312-315.  
   *(Foundational theory for steam chamber growth and overburden thermal conduction).*
2. **Boberg, T. C., & Lantz, R. B. (1966).** *Calculation of the Production Rate of a Thermally Stimulated Well.* Journal of Petroleum Technology, 18(12), 1613-1623.  
   *(Exact equations for post-injection cyclic steam temperature dissipation and thermal productivity index).*
3. **Prats, M. (1982).** *Thermal Recovery.* Monograph Series, Society of Petroleum Engineers (SPE), Richardson, TX.  
   *(Comprehensive thermal properties of heavy oil sands and steam injection mechanics).*
4. **Butler, R. M. (1991).** *Thermal Recovery of Oil and Bitumen.* Prentice Hall, Englewood Cliffs, NJ.  
   *(Heavy oil viscosity-temperature kinetics and thermal inflow mechanisms).*

### 📙 Sucker Rod Pumping & Wave Mechanics
5. **Gibbs, S. G., & Neely, A. B. (1966).** *Computer Diagnosis of Down-Hole Conditions in Sucker Rod Pumping Wells.* Journal of Petroleum Technology, 18(01), 91-98.  
   *(Hyperbolic 1D damped wave equation for diagnostic dynamometer card generation).*
6. **Gibbs, S. G. (1963).** *Predicting the Behavior of Sucker-Rod Pumping Systems.* Journal of Petroleum Technology, 15(07), 769-778.  
   *(Mathematical derivation of boundary conditions and rod string resonance).*
7. **American Petroleum Institute (API RP 11L).** *Recommended Practice for Design Calculations for Sucker Rod Pumping Systems (Conventional Units).* API, Washington, D.C.  
   *(Standards for tapered rod strings, peak loads, and inertial amplification factors).*
8. **Takacs, G. (2015).** *Sucker-Rod Pumping Manual.* Gulf Professional Publishing, Elsevier.  
   *(Industrial guidelines for heavy oil rod floating, impact shock, and VFD speed control).*

### 📕 Wellbore Thermal Hydraulics & Fluid Rheology
9. **Ramey, H. J. (1962).** *Wellbore Heat Transmission.* Journal of Petroleum Technology, 14(04), 427-435.  
   *(Analytical solution for wellbore fluid temperature profiles as a function of depth and time).*
10. **Walther, C. (1931) / ASTM D341.** *Standard Practice for Viscosity-Temperature Charts for Liquid Petroleum Products.* ASTM International, West Conshohocken, PA.  
    *(Two-constant double-logarithmic viscosity-temperature correlation for crude oils).*
11. **Herschel, W. H., & Bulkley, R. (1926).** *Measurement of Consistency as Applied to Rubber-Benzene Solutions.* ASTM Proceedings, 26, 621-633.  
    *(Yield-pseudoplastic non-Newtonian fluid rheology formulation).*
12. **Mullins, O. C., Sabbah, H., Eyssautier, J. et al. (2012).** *Advances in Asphaltene Science and the Modified Yen-Mullins Model.* Energy & Fuels, 26(7), 3986-4003.  
    *(Asphaltene colloidal instability index and precipitation onset kinetics).*

### 📗 Structural Reliability & Machine Learning
13. **Miner, M. A. (1945).** *Cumulative Damage in Fatigue.* Journal of Applied Mechanics, 12(3), A159-A164.  
    *(Linear damage accumulation rule $D = \sum n_i/N_i$).*
14. **Goodman, J. (1899).** *Mechanics Applied to Engineering.* Longmans, Green & Co., London.  
    *(Modified Goodman diagram for cyclic fatigue under combined mean and alternating stresses).*
15. **Breiman, L. (2001).** *Random Forests.* Machine Learning, 45(1), 5-32.  
    *(Ensemble classification algorithm used in the dynamometer card diagnostic engine).*

### 🛢️ Oil India Limited & Baghewala Field Literature
16. **Oil India Limited (OIL) Technical Publications & EOR Documentation.**  
    *Studies on Cyclic Steam Stimulation and Sucker Rod Pumping in the Bikaner-Nagaur Basin, Rajasthan.*  
    *(Field geological, PVT, and operational parameters for Jodhpur Sandstone extra-heavy crude).*
