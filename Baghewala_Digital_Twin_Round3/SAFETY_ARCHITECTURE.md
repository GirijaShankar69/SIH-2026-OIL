# Safety Constraint Engine & Human-in-the-Loop Architecture

## 1. Safety Philosophy
The Baghewala Digital Twin strictly adheres to the principle of **Intelligent Decision-Support with Gated Closed-Loop Control**. Autonomous AI optimization routines cannot bypass hard physical constraints or replace human engineering sign-off when critical operating envelopes are approached.

```
+--------------------------+
|  AI Joint CSS-SRP Model  |
+--------------------------+
             | (Proposes SPM / Operational Settings)
             v
+-----------------------------------+
|     Safety Constraint Engine      |
|  - Check Mechanical Limits (SPM)  |
|  - Check Stress Limits (PPRL)     |
|  - Check Fatigue Limits (Shock)   |
|  - Check Pump Hold-Down Load      |
+-----------------------------------+
             |
             +-----------------------+----------------------+
             |                       |                      |
             v                       v                      v
    [🟢 RECOMMENDED]       [🟡 APPROVAL REQ]          [🔴 BLOCKED]
    Normal Envelope        Warning / Elevated Risk    Violates API 11L
    Autonomous Execute     Requires Engineer Auth     Command Clamped
```

---

## 2. Hard & Soft Mechanical Limits

| Constraint Parameter | Threshold | Action on Breach |
|---|---|---|
| **Max Pumping Speed (SPM)** | 8.5 SPM | Hard clamp to 8.5 SPM (`BLOCKED`) |
| **Min Pumping Speed (SPM)** | 2.0 SPM | Hard clamp to 2.0 SPM (`BLOCKED`) |
| **Max Polished Rod Load (PPRL)** | 28,000 lbs | Speed increase blocked; trim speed (`BLOCKED`) |
| **Max Allowable Impact Shock** | 1,500 lbs | Speed increase blocked; trim speed (`BLOCKED`) |
| **Pump Unsetting Probability** | > 50.0% | Gated: `ENGINEER_APPROVAL_REQUIRED` |
| **Min Pump Fillage** | < 60.0% | Gated: `ENGINEER_APPROVAL_REQUIRED` |
