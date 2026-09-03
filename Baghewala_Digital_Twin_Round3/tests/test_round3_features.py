"""
Unit tests for Round 3 features:
- AI Classifier (all 8 classes & validation metrics)
- Real ML Surrogate Model
- Validation Framework & Uncertainty
- Safety Constraint Engine
- Prescriptive Maintenance
- Ambient Temperature Effects
"""
import unittest
import numpy as np

from core.ml.dyno_card_classifier import baghewala_card_classifier
from core.ml.surrogate_model import baghewala_surrogate, baghewala_accelerator
from core.validation.validation_metrics import baghewala_validation
from core.safety.safety_engine import baghewala_safety
from core.ml.predictive_maintenance import baghewala_maintenance
from core.physics.wellbore_hydraulics import baghewala_wellbore


class TestRound3Features(unittest.TestCase):

    def test_dyno_classifier_classes_and_metrics(self):
        """Verify all 8 classes are trained and validation metrics exist."""
        self.assertEqual(len(baghewala_card_classifier.CARD_CLASSES), 8)
        self.assertIn("Accuracy", baghewala_card_classifier.validation_metrics)
        self.assertIn("Confusion_Matrix", baghewala_card_classifier.validation_metrics)
        self.assertGreater(baghewala_card_classifier.validation_metrics["Accuracy"], 0.85)

    def test_surrogate_model(self):
        """Verify real Random Forest surrogate trains and predicts with uncertainty."""
        self.assertTrue(baghewala_surrogate.is_trained)
        res = baghewala_surrogate.predict(
            steam_volume_cwe=3500.0,
            soak_days=5.0,
            injection_pressure=65.0,
            cycle_number=1,
            producing_days=120,
            spm=5.5,
            ambient_temp_c=30.0
        )
        self.assertIn("cum_oil_bbl", res)
        self.assertIn("cum_oil_bbl_uncertainty", res)
        self.assertGreater(res["cum_oil_bbl"], 0.0)
        self.assertGreater(res["cum_oil_bbl_uncertainty"], 0.0)
        self.assertIn("R2", baghewala_surrogate.validation_metrics)

    def test_safety_constraint_engine(self):
        """Verify safety engine blocks unsafe operations and requires approval appropriately."""
        # Unsafe SPM (> 8.5)
        eval_blocked = baghewala_safety.evaluate_action(
            recommended_spm=10.0,
            current_state={}
        )
        self.assertEqual(eval_blocked["status"], "BLOCKED")
        self.assertEqual(eval_blocked["safe_spm"], 8.5)

        # High unsetting risk requires approval
        eval_approval = baghewala_safety.evaluate_action(
            recommended_spm=6.0,
            current_state={"unsetting_data": {"unsetting_probability_pct": 60.0}}
        )
        self.assertEqual(eval_approval["status"], "ENGINEER_APPROVAL_REQUIRED")

        # Normal condition recommended
        eval_ok = baghewala_safety.evaluate_action(
            recommended_spm=5.5,
            current_state={"unsetting_data": {"unsetting_probability_pct": 10.0}}
        )
        self.assertEqual(eval_ok["status"], "RECOMMENDED")

    def test_prescriptive_maintenance(self):
        """Verify prescriptive maintenance maps risks to actions and expected effects."""
        rul_data = {
            "rod_health_score_pct": 40.0,
            "remaining_useful_life_days": 60,
            "cumulative_fatigue_damage": 0.65
        }
        unsetting_data = {
            "unsetting_probability_pct": 45.0,
            "upward_shock_load_lbs": 3800.0
        }
        asphaltene_data = {
            "asphaltene_deposition_risk_index": 0.55,
            "colloidal_instability_index": 1.1
        }
        
        actions = baghewala_maintenance.generate_prescriptive_actions(
            rul_data=rul_data,
            unsetting_data=unsetting_data,
            asphaltene_data=asphaltene_data,
            current_spm=6.5,
            is_rod_floating=True
        )
        
        self.assertGreaterEqual(len(actions), 3)
        for act in actions:
            self.assertIn("risk", act)
            self.assertIn("mechanism", act)
            self.assertIn("recommended_action", act)
            self.assertIn("expected_effect", act)

    def test_ambient_temperature_effects(self):
        """Verify ambient temperature changes wellhead fluid temperature."""
        prof_hot = baghewala_wellbore.compute_temperature_profile(
            sandface_temp_c=120.0,
            liquid_rate_m3d=20.0,
            ambient_temp_c=45.0
        )
        prof_cold = baghewala_wellbore.compute_temperature_profile(
            sandface_temp_c=120.0,
            liquid_rate_m3d=20.0,
            ambient_temp_c=10.0
        )
        self.assertGreater(prof_hot["wellhead_temp_c"], prof_cold["wellhead_temp_c"])

    def test_data_quality_score(self):
        """Verify data quality scoring detects invalid values."""
        clean_telem = {"spm": [5.5, 6.0], "temperature_c": [80.0, 75.0]}
        corrupt_telem = {"spm": [5.5, 300.0], "temperature_c": [80.0, -150.0]}
        
        score_clean = baghewala_validation.generate_data_quality_score(clean_telem)
        score_corrupt = baghewala_validation.generate_data_quality_score(corrupt_telem)
        
        self.assertEqual(score_clean["score"], 100.0)
        self.assertLess(score_corrupt["score"], 100.0)


if __name__ == "__main__":
    unittest.main()
