# Original User Request

## 2026-08-24T11:49:51Z

Build a complete SIH 2026 presentation, dynamic project code upgrades, and automation documentation for the AI-Enabled Well-to-Surface Digital Twin for Oil India Limited's Baghewala Field, Rajasthan.

Working directory: `d:/CSS Tech project/SIH-2026-OIL`
Integrity mode: development

---

## PPT Format Reference (SIH 2026 Template — 6 Slides Max)

The official SIH 2026 template (`SIH2026-IDEA-Presentation-Format (1).pptx`) defines exactly 6 slides:

| Slide | Title | Required Content |
|-------|-------|-----------------|
| 1 | TITLE PAGE | PS ID, PS Title, Theme, PS Category, Team ID, Team Name |
| 2 | IDEA TITLE | Proposed Solution: detailed explanation, how it addresses the problem, innovation/uniqueness |
| 3 | TECHNICAL APPROACH | Technologies used, methodology/process, flow charts/images |
| 4 | FEASIBILITY AND VIABILITY | Feasibility analysis, potential challenges/risks, strategies to overcome |
| 5 | IMPACT AND BENEFITS | Impact on target audience, social/economic/environmental benefits |
| 6 | RESEARCH AND REFERENCES | Reference links and research work |

**Rules from the template:**
- Maximum 6 slides (including title)
- No paragraphs — use bullet points, diagrams, infographics
- Precise and easy-to-understand content
- Save as PDF for submission

---

## Project Context

**Problem Statement (Oil India Limited / SIH 2026):**
Baghewala Field, Rajasthan produces 17–19° API extra-heavy crude from the Jodhpur Sandstone reservoir. Reservoir is characterized by native viscosity 2,500–3,500 cP at 47°C, high asphaltene content (14.5 wt%), low reservoir pressure (110 bar), and low temperature (46–48°C). CSS (Cyclic Steam Stimulation) and SRP (Sucker Rod Pump) operations are currently optimized separately using historical experience, leading to rod floating, pump failures, high SOR (4.28), and energy waste.

**The existing project** at `d:/CSS Tech project/SIH-2026-OIL` contains:
- `app.py` — 7-tab Streamlit web application
- `core/physics/` — Boberg-Lantz thermal reservoir, Gibbs 1D wave equation, Ramey wellbore hydraulics, Herschel-Bulkley rheology
- `core/ml/` — Dyno card AI classifier (Random Forest), CSS surrogate model, joint multi-objective optimizer, predictive maintenance RUL engine
- `core/twin/digital_twin.py` — Multi-well digital twin & autonomous closed-loop VFD governor
- `core/data/sample_data_generator.py` — Calibrated synthetic Baghewala telemetry

**Verified Results from existing system:**
- +16.8% Oil Recovery, -24.5% SOR, -22.3% Lift Energy, 100% Rod Floating Eliminated
- Net economic gain: ₹38.2 Lakhs / well / cycle
- 13/13 unit tests passing

---

## Requirements

### R1. Create SIH 2026 Presentation PPT

Create a fully-filled PowerPoint file `SIH2026-Baghewala-Digital-Twin.pptx` in the working directory following the exact 6-slide SIH 2026 template structure. All 6 slides must be filled with project-specific content for the Baghewala Field AI Digital Twin. Content should be in bullet-point / infographic style (no paragraphs), technically accurate based on the existing project, and compelling for a national hackathon jury panel.

Slide-specific content guidance:
- **Slide 1 (Title Page):** Fill in: PS Category = Software, Team Name = [use placeholder "SIH-TEAM-BGW"], Theme = Smart Automation / Energy, PS Title = "AI-Enabled Integrated CSS & SRP Optimization for Heavy Oil EOR at Baghewala Field, OIL".
- **Slide 2 (Idea Title):** Highlight the integrated digital twin concept, autonomous VFD governor, and joint optimization — not available in any existing commercial tool for Indian heavy oil fields.
- **Slide 3 (Technical Approach):** List the 5-layer architecture (Thermal Reservoir → Wellbore Hydraulics → SRP Wave Dynamics → AI/ML Optimization → Digital Twin), key technologies (Python, Streamlit, Gibbs Wave Equation, Random Forest, Boberg-Lantz, Pareto Optimizer), and include a simple architecture flow diagram using PPT shapes/arrows.
- **Slide 4 (Feasibility):** Address data availability (OIL SCADA telemetry), computational feasibility (sub-ms surrogate), pilot deployment path, risks (data quality, steam injection variability), and mitigation strategies.
- **Slide 5 (Impact):** Quantify impact using verified metrics from the project (Oil gain, SOR reduction, energy savings, rod failure elimination, economic benefit per well per cycle, field-scale extrapolation). Include environmental benefit (reduced steam → reduced CO₂ from boiler).
- **Slide 6 (Research & References):** Include the 16 academic references from `MODELS_DATA_AND_SOURCES.md` in condensed form (author, year, title).

The PPT must be created programmatically using python-pptx. Read the existing template file `SIH2026-IDEA-Presentation-Format (1).pptx` to understand fonts, colors, and layout before building the new file. Use the same color scheme and style.

### R2. Upgrade Project Files for Fully Dynamic Outputs

Edit the existing Python source files so all dashboard readings, chart values, metrics, and outputs are dynamically computed from actual physics simulation calls and the digital twin state — not from hardcoded constants or static placeholder values.

Specific targets:
- **`core/data/sample_data_generator.py`**: Ensure generated telemetry is seeded with physics-derived reservoir temperature decay curves (not random), viscosity tracks via Andrade model, and SPM follows the VFD governor law.
- **`app.py`**: Ensure all KPI metric cards (SOR, BOPD, kWh/bbl, Rod Float Risk, RUL days) update dynamically when the user changes sliders or well-selector dropdowns. Remove any hardcoded numeric strings in metric display calls. Use live calls to digital twin and physics functions.
- **`core/twin/digital_twin.py`**: Add a `get_live_metrics(well_id)` method that returns a fully computed dict of current KPIs for a given well at its current simulation state (temperature, viscosity_cp, spm, fillage, pprl_lbs, rul_days, sor, rod_float_risk, pump_unsetting_prob).
- **`ui/components.py`**: Ensure all Plotly chart generators accept computed data arrays as arguments rather than generating their own placeholder data internally.

### R3. Add Well-Site Automation Guide (`WELL_SITE_AUTOMATION_GUIDE.md`)

Create a comprehensive Markdown guide in the working directory that explains:
1. **System Architecture Overview** — how the Digital Twin connects to real field equipment (SCADA, VFD drives, flow meters, pressure transducers).
2. **Step-by-Step Automation Setup** — how a field engineer can connect the digital twin to live OPC-UA / MQTT SCADA data streams from the SRP drive panels and wellhead sensors.
3. **Autonomous VFD Control Loop** — how the closed-loop VFD governor continuously reads downhole temperature (or calculates it), computes optimal SPM, and sends frequency setpoints to the drive.
4. **CSS Cycle Automation Workflow** — how the optimizer automatically recommends steam volume and soak duration at the start of each cycle, and how to integrate this with steam generator control systems.
5. **Alert & Notification System** — how to configure the AI rod floating alert, asphaltene deposition warnings, and RUL thresholds to trigger SMS/email alerts or SCADA alarms.
6. **Data Pipeline & Logging** — how to set up continuous telemetry ingestion, storage, and retraining of the dyno card classifier as new field data arrives.
7. **Operator's Quick-Reference** — one-page table: what each dashboard tab shows, what actions to take for each alert type, and escalation procedures.

---

## Acceptance Criteria

### PPT Quality
- [ ] Exactly 6 slides, matching the SIH 2026 template structure (Title, Idea, Technical, Feasibility, Impact, References)
- [ ] All placeholder text in the template is replaced with project-specific content
- [ ] At least one diagram or flow chart (using PPT shapes) on the Technical Approach slide
- [ ] All quantified metrics on Impact slide match the verified project results (16.8%, 24.5%, 22.3%, ₹38.2L)
- [ ] No paragraph blocks — all content in bullet points or visual elements
- [ ] File saved as `SIH2026-Baghewala-Digital-Twin.pptx` in the working directory

### Dynamic Code Quality
- [ ] `python -m unittest discover tests/` passes all 13 tests with exit code 0 after changes
- [ ] `python -m streamlit run app.py` starts without import errors
- [ ] No hardcoded numeric KPI strings remain in `app.py` metric display calls
- [ ] `digital_twin.get_live_metrics(well_id)` exists and returns a dict with at minimum: temperature, viscosity_cp, spm, fillage, pprl_lbs, rul_days, sor, rod_float_risk, pump_unsetting_prob
- [ ] Changing the well selector dropdown in the Streamlit app triggers a new physics computation (verified by code inspection — no static list comprehension returning fixed numbers)

### Automation Guide Quality
- [ ] `WELL_SITE_AUTOMATION_GUIDE.md` exists in working directory and is at least 800 words
- [ ] Covers all 7 sections listed in R3
- [ ] Contains at least one Mermaid architecture diagram showing the data flow from field sensors → Digital Twin → VFD control signal
- [ ] Includes concrete code/config snippets (e.g., MQTT connection setup, OPC-UA node address example, threshold configuration)
- [ ] Contains the one-page Operator Quick-Reference table
