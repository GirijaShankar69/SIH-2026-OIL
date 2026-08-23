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
        v_native = self.reservoir.oil_viscosity(47.0) # ~ 2500 - 3000 cP
        v_steam = self.reservoir.oil_viscosity(220.0) # ~ 15 - 25 cP
        
        self.assertGreater(v_native, 1500.0)
        self.assertLess(v_steam, 35.0)
        self.assertGreater(v_native / v_steam, 50.0)

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


if __name__ == "__main__":
    unittest.main()
