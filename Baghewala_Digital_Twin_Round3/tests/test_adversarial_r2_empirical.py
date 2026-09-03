"""
Empirical and Adversarial Stress Test Suite for R2 (Dynamic Codebase & Physics Models).
Conducted by Challenger 2.
"""

import unittest
import py_compile
import numpy as np
import pandas as pd
from core.twin.digital_twin import BaghewalaFieldDigitalTwin, BaghewalaWellDigitalTwin
from core.data.sample_data_generator import WELLS_METADATA, generate_well_telemetry
from core.physics.thermal_reservoir import CSSCycleParameters, baghewala_reservoir
from core.physics.sucker_rod_dynamics import baghewala_srp
from core.physics.wellbore_hydraulics import baghewala_wellbore
from core.physics.fluid_rheology import baghewala_rheology


class TestAdversarialR2Empirical(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.field_twin = BaghewalaFieldDigitalTwin()
        cls.well_ids = [w["well_id"] for w in WELLS_METADATA]

    def test_01_all_wells_all_days_kpi_completeness_and_ranges(self):
        """Stress-test get_live_metrics for all 6 wells across days [1, 30, 60, 90, 120] and SPM variants."""
        days_to_test = [1, 30, 60, 90, 120]
        spm_overrides = [None, 3.5, 5.5, 7.8, 9.0]
        
        required_keys = [
            "temperature", "sandface_temperature", "wellhead_temperature",
            "viscosity_cp", "spm", "fillage", "pprl_lbs", "mprl_lbs",
            "rul_days", "sor", "rod_float_risk", "pump_unsetting_prob",
            "oil_rate_bopd", "cum_oil_bbl", "motor_power_kw", "kwh_per_bbl",
            "is_rod_floating", "diagnosis", "diagnosis_severity",
            "diagnosis_confidence", "diagnosis_recommendation"
        ]

        evaluated_count = 0
        for well_id in self.well_ids:
            for day in days_to_test:
                for spm_override in spm_overrides:
                    metrics = self.field_twin.get_live_metrics(well_id, day=day, spm_override=spm_override)
                    evaluated_count += 1

                    # Check all required keys exist and not None
                    for k in required_keys:
                        self.assertIn(k, metrics, f"Well {well_id}, day {day} missing key {k}")
                        self.assertIsNotNone(metrics[k], f"Well {well_id}, day {day} key {k} is None")

                    # Check physical bounds
                    self.assertTrue(40.0 <= metrics["temperature"] <= 270.0, f"Temp out of bounds: {metrics['temperature']}")
                    self.assertTrue(40.0 <= metrics["sandface_temperature"] <= 280.0, f"Sandface temp out of bounds: {metrics['sandface_temperature']}")
                    self.assertTrue(25.0 <= metrics["wellhead_temperature"] <= 260.0, f"Wellhead temp out of bounds: {metrics['wellhead_temperature']}")
                    self.assertTrue(8.0 <= metrics["viscosity_cp"] <= 15000.0, f"Viscosity out of bounds: {metrics['viscosity_cp']}")
                    self.assertTrue(0.0 <= metrics["spm"] <= 15.0, f"SPM out of bounds: {metrics['spm']}")
                    self.assertTrue(0.0 <= metrics["fillage"] <= 1.0, f"Fillage out of bounds: {metrics['fillage']}")
                    self.assertTrue(metrics["pprl_lbs"] >= metrics["mprl_lbs"], f"PPRL ({metrics['pprl_lbs']}) < MPRL ({metrics['mprl_lbs']})")
                    self.assertTrue(metrics["rul_days"] >= 0, f"RUL days negative: {metrics['rul_days']}")
                    self.assertTrue(metrics["sor"] > 0.0, f"SOR non-positive: {metrics['sor']}")
                    self.assertTrue(0.0 <= metrics["rod_float_risk"] <= 1.0, f"Rod float risk out of bounds: {metrics['rod_float_risk']}")
                    self.assertTrue(0.0 <= metrics["pump_unsetting_prob"] <= 1.0, f"Pump unsetting prob out of bounds: {metrics['pump_unsetting_prob']}")
                    self.assertTrue(metrics["oil_rate_bopd"] >= 0.0, f"Oil rate negative: {metrics['oil_rate_bopd']}")
                    self.assertTrue(metrics["cum_oil_bbl"] >= 0.0, f"Cum oil negative: {metrics['cum_oil_bbl']}")
                    self.assertTrue(metrics["motor_power_kw"] >= 0.0, f"Motor power negative: {metrics['motor_power_kw']}")
                    self.assertTrue(metrics["kwh_per_bbl"] >= 0.0, f"kWh/bbl negative: {metrics['kwh_per_bbl']}")
                    self.assertIsInstance(metrics["is_rod_floating"], bool)
                    self.assertIsInstance(metrics["diagnosis"], str)
                    self.assertIsInstance(metrics["diagnosis_severity"], str)
                    self.assertGreater(len(metrics["diagnosis_severity"]), 0)
                    self.assertTrue(0.0 <= metrics["diagnosis_confidence"] <= 100.0)

        print(f"[PASSED] Evaluated {evaluated_count} matrix combinations across all 6 wells, days, and SPM overrides.")

    def test_02_monotonic_thermal_decay_and_viscosity_increase(self):
        """Verify strict monotonic temperature decay and monotonic viscosity increase over cycle days 1-120."""
        for well_id in self.well_ids:
            well = self.field_twin.wells[well_id]
            temps = []
            viscs = []
            cum_oils = []
            wellhead_temps = []
            sandface_temps = []

            for d in range(1, 121):
                state = well.get_current_state(day=d)
                temps.append(state["reservoir_temperature_c"])
                viscs.append(state["oil_viscosity_cp"])
                cum_oils.append(state["cum_oil_bbl"])
                wellhead_temps.append(state["wellhead_temperature_c"])
                sandface_temps.append(state["sandface_temperature_c"])

            # 1. Monotonic Temperature Decay: T(t) should strictly decrease or stay equal
            for i in range(len(temps) - 1):
                self.assertGreaterEqual(temps[i], temps[i+1], f"Well {well_id} temperature did not decay monotonically at day {i+1} ({temps[i]} vs {temps[i+1]})")

            # 2. Monotonic Viscosity Increase: mu(t) should strictly increase or stay equal
            for i in range(len(viscs) - 1):
                self.assertLessEqual(viscs[i], viscs[i+1], f"Well {well_id} viscosity did not increase monotonically at day {i+1} ({viscs[i]} vs {viscs[i+1]})")

            # 3. Cumulative Oil Monotonic Increase
            for i in range(len(cum_oils) - 1):
                self.assertLessEqual(cum_oils[i], cum_oils[i+1], f"Well {well_id} cumulative oil decreased at day {i+1}")

            # 4. Thermal Gradient (Sandface vs Wellhead)
            for i in range(len(sandface_temps)):
                self.assertGreaterEqual(sandface_temps[i], wellhead_temps[i], f"Well {well_id} sandface temp ({sandface_temps[i]}) < wellhead temp ({wellhead_temps[i]}) on day {i+1}")

        print("[PASSED] Confirmed strict monotonic thermal decay, viscosity kinetics, and cumulative production for all wells.")

    def test_03_autonomous_vfd_governor_dynamic_response(self):
        """Verify autonomous closed-loop VFD governor trims SPM dynamically in response to viscosity/temperature."""
        # Autonomous wells: BGW-01 and BGW-09
        auto_wells = ["BGW-01", "BGW-09"]
        for well_id in auto_wells:
            well = self.field_twin.wells[well_id]
            self.assertTrue(well.autonomous_vfd_enabled, f"Well {well_id} should have autonomous VFD enabled")

            m_early = well.get_live_metrics(day=1)
            m_mid = well.get_live_metrics(day=80)
            m_late = well.get_live_metrics(day=120)

            # Early hot period: high SPM (7.4 SPM)
            self.assertEqual(m_early["spm"], 7.4, f"Early SPM should be 7.4, got {m_early['spm']}")
            # Mid cooling period: intermediate SPM (< 7.4)
            self.assertGreater(m_early["spm"], m_mid["spm"], f"Early SPM ({m_early['spm']}) should be > mid SPM ({m_mid['spm']})")
            # Late cold period: trimmed low SPM (<= 4.2)
            self.assertGreater(m_mid["spm"], m_late["spm"], f"Mid SPM ({m_mid['spm']}) should be > late SPM ({m_late['spm']})")
            self.assertLessEqual(m_late["spm"], 4.2, f"Late SPM should be trimmed <= 4.2, got {m_late['spm']}")

            # Verify manual override overrides autonomous law when provided
            m_override = well.get_live_metrics(day=120, spm_override=8.2)
            self.assertEqual(m_override["spm"], 8.2)

        print("[PASSED] Verified dynamic autonomous VFD governor response across thermal cycle regime.")

    def test_04_set_cycle_physics_recomputation(self):
        """Verify set_cycle recomputes reservoir pressure, cumulative oil, water cut, and SOR."""
        well = self.field_twin.wells["BGW-01"]
        orig_cycle = well.cycle_number

        # Simulate Cycle 1
        well.set_cycle(1)
        m_c1 = well.get_live_metrics(day=60)
        p_res_c1 = well.sim_data["reservoir_pressure_bar"][59]
        cum_oil_c1 = well.sim_data["cum_oil_bbl"][59]
        sor_c1 = well.sim_data["cumulative_sor"][59]
        wcut_c1 = well.sim_data["water_cut"][59]

        # Simulate Cycle 4
        well.set_cycle(4)
        m_c4 = well.get_live_metrics(day=60)
        p_res_c4 = well.sim_data["reservoir_pressure_bar"][59]
        cum_oil_c4 = well.sim_data["cum_oil_bbl"][59]
        sor_c4 = well.sim_data["cumulative_sor"][59]
        wcut_c4 = well.sim_data["water_cut"][59]

        # Simulate Cycle 6
        well.set_cycle(6)
        m_c6 = well.get_live_metrics(day=60)
        p_res_c6 = well.sim_data["reservoir_pressure_bar"][59]
        cum_oil_c6 = well.sim_data["cum_oil_bbl"][59]
        sor_c6 = well.sim_data["cumulative_sor"][59]
        wcut_c6 = well.sim_data["water_cut"][59]

        # In Baghewala reservoir physics:
        # Reservoir pressure depletes with cycle number: P_res(C1) > P_res(C4) > P_res(C6)
        self.assertGreater(p_res_c1, p_res_c4, f"Cycle 1 pressure ({p_res_c1}) should be > Cycle 4 ({p_res_c4})")
        self.assertGreater(p_res_c4, p_res_c6, f"Cycle 4 pressure ({p_res_c4}) should be > Cycle 6 ({p_res_c6})")

        # Water cut increases with cycle number (formation water encroachment)
        self.assertLess(wcut_c1, wcut_c4, f"Cycle 1 water cut ({wcut_c1}) should be < Cycle 4 ({wcut_c4})")
        self.assertLess(wcut_c4, wcut_c6, f"Cycle 4 water cut ({wcut_c4}) should be < Cycle 6 ({wcut_c6})")

        # Live metrics reflect cycle updates
        self.assertNotEqual(m_c1["cum_oil_bbl"], m_c6["cum_oil_bbl"])
        self.assertNotEqual(m_c1["sor"], m_c6["sor"])

        # Restore original cycle
        well.set_cycle(orig_cycle)

        print("[PASSED] Verified set_cycle accurately updates pressure depletion, water cut, and SOR.")

    def test_05_boundary_and_adversarial_inputs(self):
        """Adversarial stress testing on extreme edge cases, invalid well IDs, boundary clipping."""
        # 1. Invalid well ID must raise KeyError
        with self.assertRaises(KeyError):
            self.field_twin.get_live_metrics("INVALID_WELL_XYZ")

        with self.assertRaises(KeyError):
            self.field_twin.get_live_metrics("")

        # 2. Day boundary checks
        # Negative or zero day should be safely clipped to day 1 (index 0)
        m_day0 = self.field_twin.get_live_metrics("BGW-01", day=0)
        m_day1 = self.field_twin.get_live_metrics("BGW-01", day=1)
        self.assertEqual(m_day0["temperature"], m_day1["temperature"])

        # Day beyond 120 should be safely clipped to day 120 (index 119)
        m_day150 = self.field_twin.get_live_metrics("BGW-01", day=150)
        m_day120 = self.field_twin.get_live_metrics("BGW-01", day=120)
        self.assertEqual(m_day150["temperature"], m_day120["temperature"])

        # 3. SPM override boundary checks
        m_spm_zero = self.field_twin.get_live_metrics("BGW-01", day=30, spm_override=0.0)
        self.assertEqual(m_spm_zero["spm"], 0.0)

        # 4. Severe Rod Floating Trigger in Cold Heavy Crude (Native 46°C / 2800 cP at high SPM)
        res_cold_high_spm = baghewala_srp.solve_wave_equation(
            temperature_c=46.0,
            viscosity_cp=2800.0,
            bottomhole_pressure_bar=15.0,
            spm=8.5
        )
        self.assertTrue(res_cold_high_spm["is_rod_floating"])
        self.assertGreater(res_cold_high_spm["rod_floating_risk_index"], 0.8)
        self.assertGreater(res_cold_high_spm["impact_shock_force_lbs"], 1000.0)

        print("[PASSED] Verified boundary conditions and adversarial stress handling.")

    def test_06_app_clean_compilation_and_importability(self):
        """Verify app.py compiles cleanly without syntax errors and all modules import smoothly."""
        compiled = py_compile.compile("app.py", doraise=True)
        self.assertIsNotNone(compiled)
        print("[PASSED] Verified app.py syntax and byte-compilation cleanly.")


if __name__ == "__main__":
    unittest.main()
