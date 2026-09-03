"""
Unit Tests for Sucker Rod Dynamics, Rod Floating Detection, and AI Dyno Card Classification.
"""

import unittest
import numpy as np
from core.physics.sucker_rod_dynamics import SuckerRodDynamicsEngine, SRPConfiguration
from core.ml.dyno_card_classifier import DynoCardAIClassifier


class TestSRPDynamics(unittest.TestCase):

    def setUp(self):
        self.srp = SuckerRodDynamicsEngine()
        self.classifier = DynoCardAIClassifier()

    def test_rod_weight_and_buoyancy(self):
        """Buoyant weight in oil must be less than weight in air."""
        weights = self.srp.calculate_total_rod_weight()
        self.assertGreater(weights["total_weight_air_lbs"], 4500.0)
        self.assertLess(weights["total_weight_fluid_lbs"], weights["total_weight_air_lbs"])

    def test_rod_floating_trigger_under_high_viscosity(self):
        """High crude viscosity and high SPM must trigger rod floating condition."""
        # Hot fluid, moderate SPM -> NO rod floating
        res_hot = self.srp.solve_wave_equation(
            temperature_c=180.0,
            viscosity_cp=22.0,
            bottomhole_pressure_bar=20.0,
            spm=5.5
        )
        self.assertFalse(res_hot["is_rod_floating"])
        self.assertLess(res_hot["rod_floating_risk_index"], 0.4)

        # Cold heavy crude, high SPM -> SEVERE rod floating & impact
        res_cold = self.srp.solve_wave_equation(
            temperature_c=46.0,
            viscosity_cp=2800.0,
            bottomhole_pressure_bar=15.0,
            spm=8.5
        )
        self.assertTrue(res_cold["is_rod_floating"])
        self.assertGreater(res_cold["rod_floating_risk_index"], 0.8)
        self.assertGreater(res_cold["impact_shock_force_lbs"], 1000.0)

    def test_dynamometer_card_geometry(self):
        """Dynamometer card must return valid closed coordinates and non-zero peak loads."""
        res = self.srp.solve_wave_equation(
            temperature_c=110.0,
            viscosity_cp=90.0,
            bottomhole_pressure_bar=22.0,
            spm=6.0
        )
        self.assertEqual(len(res["surface_position_in"]), len(res["surface_load_lbs"]))
        self.assertGreater(res["pprl_lbs"], res["mprl_lbs"])
        self.assertGreater(res["prhp"], 0.0)
        self.assertGreater(res["rod_loading_pct"], 10.0)

    def test_ai_dyno_card_classifier(self):
        """AI Classifier should correctly categorize normal vs rod floating cards."""
        # 1. Normal card
        res_norm = self.srp.solve_wave_equation(temperature_c=150.0, viscosity_cp=30.0, bottomhole_pressure_bar=25.0, spm=5.0)
        diag_norm = self.classifier.classify_card(res_norm["surface_position_in"], res_norm["surface_load_lbs"])
        self.assertEqual(diag_norm["severity"], "OPTIMAL")

        # 2. Rod float card
        res_float = self.srp.solve_wave_equation(temperature_c=46.0, viscosity_cp=3200.0, bottomhole_pressure_bar=15.0, spm=8.5)
        diag_float = self.classifier.classify_card(
            res_float["surface_position_in"], 
            res_float["surface_load_lbs"],
            is_phys_floating=res_float["is_rod_floating"],
            floating_risk=res_float["rod_floating_risk_index"]
        )
        self.assertIn("Rod Floating", diag_float["diagnosis"])
        self.assertIn("CRITICAL", diag_float["severity"])


if __name__ == "__main__":
    unittest.main()
