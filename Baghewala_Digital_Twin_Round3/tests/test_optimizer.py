"""
Unit Tests for Joint Optimizer, Predictive Maintenance, and Multi-Well Digital Twin.
"""

import unittest
import numpy as np
from core.ml.joint_optimizer import JointCSSSRPOptimizer
from core.ml.predictive_maintenance import PredictiveMaintenanceEngine
from core.twin.digital_twin import BaghewalaFieldDigitalTwin


class TestOptimizerAndTwin(unittest.TestCase):

    def setUp(self):
        self.optimizer = JointCSSSRPOptimizer()
        self.maintenance = PredictiveMaintenanceEngine()
        self.field_twin = BaghewalaFieldDigitalTwin()

    def test_dynamic_spm_schedule_generation(self):
        """Dynamic SPM schedule should decrease as well cools down."""
        temps = np.linspace(200.0, 48.0, 100)
        viscs = np.logspace(1.3, 3.4, 100) # 20 cP to 2500 cP
        spm_sched = self.optimizer.generate_dynamic_spm_schedule(temps, viscs)

        self.assertEqual(len(spm_sched), 100)
        self.assertGreater(spm_sched[0], spm_sched[-1])
        self.assertTrue(np.all(spm_sched >= 3.0) and np.all(spm_sched <= 8.0))

    def test_cycle_optimization_comparison(self):
        """AI optimization must achieve higher profit, lower SOR, and fewer rod floating days than baseline."""
        comp = self.optimizer.run_cycle_comparison(
            cycle_number=1,
            steam_volume_baseline=4000.0,
            soak_days_baseline=7.0,
            spm_baseline=6.0,
            steam_volume_opt=3400.0,
            soak_days_opt=5.0,
            producing_days=100
        )

        kpis = comp["kpi_improvements"]
        self.assertGreater(kpis["profit_gain_usd"], 0.0)
        self.assertGreater(kpis["sor_reduction_pct"], 0.0)
        self.assertGreaterEqual(kpis["rod_floating_days_prevented"], 0)

    def test_predictive_maintenance_rul(self):
        """RUL calculation must output valid damage percentage and health score."""
        n_days = 90
        spm_hist = np.full(n_days, 5.5)
        s_max = np.full(n_days, 28000.0)
        s_min = np.full(n_days, 8000.0)
        impact_hist = np.zeros(n_days)
        
        rul_res = self.maintenance.estimate_rod_fatigue_and_rul(
            daily_spm_history=spm_hist,
            daily_sigma_max_psi=s_max,
            daily_sigma_min_psi=s_min,
            daily_impact_lbs=impact_hist,
            cumulative_days_in_service=120
        )

        self.assertGreater(rul_res["rod_health_score_pct"], 0.0)
        self.assertGreater(rul_res["remaining_useful_life_days"], 50)

    def test_field_digital_twin_aggregation(self):
        """Field digital twin should successfully aggregate all 6 Baghewala wells."""
        summary = self.field_twin.get_field_summary()
        self.assertEqual(summary["total_wells"], 6)
        self.assertGreater(summary["total_oil_bopd"], 50.0)
        self.assertGreater(summary["field_average_sor"], 1.5)
        self.assertEqual(len(summary["well_states"]), 6)

    def test_well_digital_twin_live_metrics_and_cycle_update(self):
        """Live metrics must return all required keys and set_cycle must dynamically update simulation."""
        metrics = self.field_twin.get_live_metrics("BGW-01", day=45)
        required_keys = [
            "temperature", "viscosity_cp", "spm", "fillage", "pprl_lbs",
            "rul_days", "sor", "rod_float_risk", "pump_unsetting_prob"
        ]
        for key in required_keys:
            self.assertIn(key, metrics, f"Missing required KPI key: {key}")
            self.assertIsNotNone(metrics[key])

        well = self.field_twin.wells["BGW-01"]
        orig_cycle = well.cycle_number
        well.set_cycle(5)
        self.assertEqual(well.cycle_number, 5)
        self.assertEqual(well.params.cycle_number, 5)
        # Restore
        well.set_cycle(orig_cycle)

        # Test invalid well raises KeyError
        with self.assertRaises(KeyError):
            self.field_twin.get_live_metrics("NON-EXISTENT-WELL")


if __name__ == "__main__":
    unittest.main()
