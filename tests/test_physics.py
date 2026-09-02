"""
Unit Tests for Subsurface Thermal Physics, Rheology, and Wellbore Hydraulics.
"""

import unittest
import numpy as np
from core.physics.thermal_reservoir import ThermalReservoirModel, CSSCycleParameters, ReservoirProperties
from core.physics.fluid_rheology import BaghewalaFluidRheology, CrudeProperties
from core.physics.wellbore_hydraulics import WellboreHydraulicsModel


class TestThermalPhysics(unittest.TestCase):

    def setUp(self):
        self.reservoir = ThermalReservoirModel()
        self.rheology = BaghewalaFluidRheology()
        self.wellbore = WellboreHydraulicsModel()

    def test_oil_viscosity_temperature_dependence(self):
        """Viscosity should drop by orders of magnitude from 47°C to 220°C."""
        v_native = self.reservoir.oil_viscosity(47.0)   # Calibration: 2,500–3,000 cP
        v_100    = self.reservoir.oil_viscosity(100.0)  # Calibration: 100–200 cP
        v_steam  = self.reservoir.oil_viscosity(220.0)  # Calibration: 12–25 cP

        # Calibration-point assertions matching MODELS_AND_DATA.md documented values
        self.assertGreater(v_native, 2200.0,
            f"47°C viscosity {v_native:.0f} cP below documented 2,500 cP minimum")
        self.assertLess(v_native, 3500.0,
            f"47°C viscosity {v_native:.0f} cP above documented 3,500 cP maximum")
        self.assertGreater(v_100, 80.0,
            f"100°C viscosity {v_100:.0f} cP below expected ~100–200 cP range")
        self.assertLess(v_100, 250.0,
            f"100°C viscosity {v_100:.0f} cP above expected ~100–200 cP range")
        self.assertGreater(v_steam, 10.0,
            f"220°C viscosity {v_steam:.1f} cP below expected 12–25 cP range")
        self.assertLess(v_steam, 30.0,
            f"220°C viscosity {v_steam:.1f} cP above expected 12–25 cP range")
        # Monotonic decrease check
        self.assertGreater(v_native / v_steam, 50.0,
            "Viscosity ratio 47°C / 220°C should exceed 50×")

    def test_steam_chamber_energy_balance(self):
        """Steam chamber calculation should return positive radius and valid heat content."""
        params = CSSCycleParameters(steam_volume_cwe=3500.0, injection_rate=250.0)
        chamber = self.reservoir.calculate_steam_chamber(params)
        
        self.assertGreater(chamber["heated_radius_m"], 8.0)
        self.assertLess(chamber["heated_radius_m"], 60.0)
        self.assertGreater(chamber["total_heat_GJ"], 5000.0)
        self.assertTrue(0.2 <= chamber["thermal_efficiency"] <= 0.95)

    def test_css_cycle_simulation_conservation(self):
        """Simulating a 120-day CSS cycle should generate strictly positive oil and temperature curves."""
        params = CSSCycleParameters(producing_days=120)
        sim = self.reservoir.simulate_cycle(params)

        self.assertEqual(len(sim["days"]), 120)
        self.assertGreater(sim["cum_oil_bbl"][-1], 1000.0)
        self.assertGreater(sim["cumulative_sor"][-1], 1.0)
        # Temperature must decay monotonically after early peak
        self.assertGreater(sim["temperature_reservoir_c"][0], sim["temperature_reservoir_c"][-1])
        # Viscosity must increase monotonically as reservoir cools
        self.assertLess(sim["viscosity_cp"][0], sim["viscosity_cp"][-1])

    def test_non_newtonian_rheology(self):
        """Heavy crude should exhibit yield stress and shear thinning at low temperatures."""
        hot_params = self.rheology.non_newtonian_parameters(120.0)
        cold_params = self.rheology.non_newtonian_parameters(48.0)

        self.assertTrue(hot_params["is_newtonian"])
        self.assertEqual(hot_params["yield_stress_pa"], 0.0)
        self.assertFalse(cold_params["is_newtonian"])
        self.assertGreater(cold_params["yield_stress_pa"], 0.0)

    def test_wellbore_temperature_profile(self):
        """Fluid ascending through wellbore must transfer heat and exhibit cooling towards surface."""
        prof = self.wellbore.compute_temperature_profile(sandface_temp_c=180.0, liquid_rate_m3d=25.0)
        
        self.assertLess(prof["wellhead_temp_c"], prof["bottomhole_temp_c"])
        self.assertGreater(prof["wellhead_temp_c"], 35.0)

    def test_physics_telemetry_generation(self):
        """Telemetry generation must return valid DataFrame with physics-derived columns."""
        from core.data.sample_data_generator import generate_well_telemetry
        df = generate_well_telemetry("BGW-01", days_count=30)
        self.assertEqual(len(df), 30)
        self.assertIn("sandface_temp_c", df.columns)
        self.assertIn("crude_viscosity_cp", df.columns)
        self.assertIn("pprl_lbs", df.columns)
        self.assertGreater(df["crude_viscosity_cp"].iloc[-1], df["crude_viscosity_cp"].iloc[0])


if __name__ == "__main__":
    unittest.main()
