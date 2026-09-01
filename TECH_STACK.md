# 🛠️ Tech Stack Reference
## AI-Enabled Well-to-Surface Digital Twin — Baghewala Field
### Oil India Limited | SIH 2026

---

## 🐍 Core Language

| Technology | Version | Where Used |
|-----------|---------|-----------|
| **Python** | 3.13.2 | Entire backend — physics engines, ML models, digital twin, data generation, dashboard |

---

## 📊 Data & Scientific Computing

| Library | Version | Where Used |
|---------|---------|-----------|
| **NumPy** | 2.5.2 | Finite-difference PDE solver (Gibbs wave equation), array operations across all physics modules, matrix computations in optimizer |
| **Pandas** | 3.0.5 | Telemetry time-series DataFrames, CSV export, well metadata tables, production history logs |
| **SciPy** | 1.18.1 | Interpolation (`interp1d`) in thermal reservoir model, complementary error function (`erfc`) for Marx-Langenheim thermal efficiency, signal smoothing in VFD governor |

**Files:** `core/physics/thermal_reservoir.py`, `core/physics/sucker_rod_dynamics.py`, `core/ml/joint_optimizer.py`, `core/data/sample_data_generator.py`

---

## 🤖 Machine Learning

| Library | Version | Where Used |
|---------|---------|-----------|
| **scikit-learn** | 1.9.0 | `RandomForestClassifier` (60 estimators) — Dynamometer Card AI Diagnostic Engine |

**File:** `core/ml/dyno_card_classifier.py`
**Task:** Classifies surface dynamometer cards into 8 operating regimes (Normal Fillage, Rod Floating, Fluid Pound, Gas Interference, Unanchored Tubing, Valve Leaks, Pump Off)

---

## 🌐 Web Application & Dashboard

| Library | Version | Where Used |
|---------|---------|-----------|
| **Streamlit** | 1.62.0 | 7-tab interactive web dashboard, sidebar controls, metric cards, `st.session_state` lazy download pattern, `st.download_button` |
| **Plotly** | 6.9.0 | All interactive charts — 3D steam chamber isotherm maps, surface & downhole dynamometer cards, wellbore gradient profiles, Goodman fatigue diagrams, Pareto frontier plots, field GIS map |

**Files:** `app.py`, `ui/components.py`, `ui/styles.py`

---

## 🏗️ Project File Structure & Where Each Tech is Applied

```
SIH-2026-OIL/
│
├── app.py                          ← Streamlit, Plotly, Pandas
│
├── core/
│   ├── physics/
│   │   ├── thermal_reservoir.py    ← NumPy, SciPy (erfc, interp1d)
│   │   ├── sucker_rod_dynamics.py  ← NumPy (finite-difference PDE)
│   │   ├── fluid_rheology.py       ← NumPy
│   │   └── wellbore_hydraulics.py  ← NumPy
│   │
│   ├── ml/
│   │   ├── dyno_card_classifier.py ← scikit-learn (RandomForest), NumPy
│   │   ├── surrogate_model.py      ← NumPy, SciPy
│   │   ├── joint_optimizer.py      ← NumPy, SciPy
│   │   └── predictive_maintenance.py ← NumPy
│   │
│   ├── twin/
│   │   └── digital_twin.py         ← NumPy, all physics + ML modules
│   │
│   └── data/
│       └── sample_data_generator.py ← NumPy, Pandas
│
├── ui/
│   ├── components.py               ← Plotly (go.Figure, go.Scatter3d, etc.)
│   └── styles.py                   ← HTML/CSS (inline Streamlit markdown)
│
├── tests/
│   ├── test_physics.py             ← Python unittest
│   ├── test_dynamics.py            ← Python unittest
│   └── test_optimizer.py           ← Python unittest
│
├── export_jury_datasets.py         ← Pandas, NumPy
└── requirements.txt                ← pip dependency list
```

---

## 🧪 Testing

| Tool | Where Used |
|------|-----------|
| **Python `unittest`** (stdlib) | 30 automated unit tests across physics, SRP dynamics, ML optimizer, and digital twin aggregation — `tests/test_physics.py`, `tests/test_dynamics.py`, `tests/test_optimizer.py` |

---

## 📄 Document Generation

| Library | Version | Where Used |
|---------|---------|-----------|
| **python-pptx** | 1.0.2 | Programmatic generation of `SIH2026-Baghewala-Digital-Twin.pptx` — 6-slide SIH 2026 presentation with layout, shapes, text boxes, and architecture diagrams |

**File:** `SIH2026-Baghewala-Digital-Twin.pptx` (generated via `generate_presentation.py`)

---

## 🗂️ Version Control

| Tool | Where Used |
|------|-----------|
| **Git** | Source control for the entire project — branch `main`, hosted at `d:/CSS Tech project/SIH-2026-OIL/.git` |

---

## 🖥️ Runtime Environment

| Component | Detail |
|-----------|--------|
| **OS** | Windows 11 |
| **Shell** | PowerShell / Command Prompt |
| **Python Runtime** | CPython 3.13.2 — `C:\Python313\python.exe` |
| **Package Manager** | pip 26.x |
| **Server** | Uvicorn (bundled with Streamlit) — serves on `localhost:8501` |
| **Browser** | Any modern browser → `http://localhost:8501` |

---

## 🚀 Quick Install & Run

```bash
# Install all dependencies
pip install -r requirements.txt

# Launch the dashboard
python -m streamlit run app.py --server.port 8501

# Run all tests
python -m unittest discover tests/

# Export jury datasets
python export_jury_datasets.py
```
