"""
Physics-Informed Surrogate Model for Rapid CSS Cycle Evaluation
Allows millisecond-scale evaluation of multi-cycle thermal recovery and economics.
"""

import numpy as np
from typing import Dict, Any, List
from core.physics.thermal_reservoir import ThermalReservoirModel, CSSCycleParameters, baghewala_reservoir


class CSSPhysicsSurrogateModel:
    """
    Surrogate model for rapid thermal and production forecasting.
    """

    def __init__(self, reservoir_model: ThermalReservoirModel = None):
        self.res_model = reservoir_model or baghewala_reservoir

    def predict_cycle_performance(self, 
                                  steam_volume_cwe: float, 
                                  soak_days: float, 
                                  injection_pressure: float,
                                  cycle_number: int = 1,
                                  producing_days: int = 120,
                                  spm: float = 5.5) -> Dict[str, Any]:
        """
        Fast evaluation of a CSS cycle parameters.
        """
        params = CSSCycleParameters(
            cycle_number=cycle_number,
            steam_volume_cwe=steam_volume_cwe,
            injection_rate=250.0,
            steam_quality=0.78,
            steam_temperature=265.0,
            injection_pressure=injection_pressure,
            soak_days=soak_days,
            producing_days=producing_days,
            bottomhole_flowing_pressure=18.0
        )

        sim_res = self.res_model.simulate_cycle(params)

        cum_oil_m3 = float(sim_res["cum_oil_m3"][-1])
        cum_oil_bbl = float(sim_res["cum_oil_bbl"][-1])
        cum_water_m3 = float(sim_res["cum_water_m3"][-1])
        final_sor = float(sim_res["cumulative_sor"][-1])
        peak_oil_bopd = float(np.max(sim_res["oil_rate_bopd"]))
        avg_oil_bopd = float(np.mean(sim_res["oil_rate_bopd"]))

        # Economic calculation (in USD / INR)
        # Oil price: $75 / bbl (~ ₹6,200 / bbl)
        # Steam generation cost: $22 / m3 CWE (~ ₹1,800 / m3)
        # Lifting / electricity cost: $0.12 / kWh (~ ₹10 / kWh)
        oil_revenue_usd = cum_oil_bbl * 75.0
        steam_cost_usd = steam_volume_cwe * 22.0
        lifting_energy_kwh = cum_oil_bbl * (3.8 + 0.15 * spm) # kWh
        lifting_cost_usd = lifting_energy_kwh * 0.12
        net_profit_usd = oil_revenue_usd - steam_cost_usd - lifting_cost_usd

        # Optimal cut-off day (when daily revenue < daily operating cost + incremental steam value)
        daily_revenue = sim_res["oil_rate_bopd"] * 75.0
        daily_lifting_cost = (sim_res["oil_rate_bopd"] * 4.5) * 0.12 + 120.0 # $120 fixed daily OPEX
        economic_profit = daily_revenue - daily_lifting_cost
        
        # Cut-off day where daily profit drops below $80/day
        cut_off_candidates = np.where(economic_profit < 80.0)[0]
        optimal_cutoff_day = int(cut_off_candidates[0] + 1) if len(cut_off_candidates) > 0 else producing_days

        return {
            "cum_oil_m3": cum_oil_m3,
            "cum_oil_bbl": cum_oil_bbl,
            "cum_water_m3": cum_water_m3,
            "cumulative_sor": final_sor,
            "peak_oil_bopd": peak_oil_bopd,
            "avg_oil_bopd": avg_oil_bopd,
            "optimal_cutoff_day": optimal_cutoff_day,
            "oil_revenue_usd": oil_revenue_usd,
            "steam_cost_usd": steam_cost_usd,
            "lifting_cost_usd": lifting_cost_usd,
            "net_profit_usd": net_profit_usd,
            "net_profit_inr_lakhs": (net_profit_usd * 83.5) / 100000.0,
            "simulation_raw": sim_res
        }


# Global surrogate instance
baghewala_surrogate = CSSPhysicsSurrogateModel()
