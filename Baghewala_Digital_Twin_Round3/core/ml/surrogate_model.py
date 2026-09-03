"""
Surrogate Model Framework for Baghewala Field
Contains:
1. CSSPhysicsAccelerator: Physics-informed analytical computational accelerator.
2. CSSRandomForestSurrogate: True Machine Learning surrogate trained on physics simulations.
"""

import numpy as np
import time
from typing import Dict, Any, List
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from core.physics.thermal_reservoir import ThermalReservoirModel, CSSCycleParameters, baghewala_reservoir
from core.validation.validation_metrics import baghewala_validation


class CSSPhysicsAccelerator:
    """
    Physics-informed computational accelerator for rapid CSS cycle evaluation.
    Directly leverages vectorized analytical solutions of Boberg-Lantz thermal kinetics.
    """

    def __init__(self, reservoir_model: ThermalReservoirModel = None):
        self.res_model = reservoir_model or baghewala_reservoir

    def predict_cycle_performance(self, 
                                  steam_volume_cwe: float, 
                                  soak_days: float, 
                                  injection_pressure: float,
                                  cycle_number: int = 1,
                                  producing_days: int = 120,
                                  spm: float = 5.5,
                                  ambient_temp_c: float = 30.0) -> Dict[str, Any]:
        """
        Fast evaluation of a CSS cycle parameters using analytical physics.
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

        sim_res = self.res_model.simulate_cycle(params, ambient_temp_c=ambient_temp_c)

        cum_oil_m3 = float(sim_res["cum_oil_m3"][-1])
        cum_oil_bbl = float(sim_res["cum_oil_bbl"][-1])
        cum_water_m3 = float(sim_res["cum_water_m3"][-1])
        final_sor = float(sim_res["cumulative_sor"][-1])
        peak_oil_bopd = float(np.max(sim_res["oil_rate_bopd"]))
        avg_oil_bopd = float(np.mean(sim_res["oil_rate_bopd"]))

        # Economic calculation (Net profit proxy)
        oil_revenue_usd = cum_oil_bbl * 75.0
        steam_cost_usd = steam_volume_cwe * 22.0
        lifting_energy_kwh = cum_oil_bbl * (3.8 + 0.15 * spm) # kWh
        lifting_cost_usd = lifting_energy_kwh * 0.12
        net_profit_usd = oil_revenue_usd - steam_cost_usd - lifting_cost_usd

        daily_revenue = sim_res["oil_rate_bopd"] * 75.0
        daily_lifting_cost = (sim_res["oil_rate_bopd"] * 4.5) * 0.12 + 120.0
        economic_profit = daily_revenue - daily_lifting_cost
        
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


class CSSRandomForestSurrogate:
    """
    Trained Multi-Output Machine Learning Surrogate Model for CSS Performance Forecasting.
    Uses Random Forest Regression to predict Cumulative Oil, Peak Oil, SOR, and Economic Profit.
    """

    def __init__(self, reservoir_model: ThermalReservoirModel = None):
        self.res_model = reservoir_model or baghewala_reservoir
        self.model = RandomForestRegressor(n_estimators=40, random_state=42)
        self.is_trained = False
        self.validation_metrics = {}
        self.train_surrogate()

    def train_surrogate(self):
        """Generates training data via physics sweeps and fits the Random Forest Regressor."""
        X = []
        y = []
        accelerator = CSSPhysicsAccelerator(self.res_model)

        # Parameter sweeps: steam_vol, soak, inj_p, cycle, prod_days, spm, ambient_t
        for steam_vol in [2000.0, 3000.0, 4000.0, 5000.0]:
            for soak in [3.0, 5.0, 8.0]:
                for inj_p in [55.0, 65.0, 75.0]:
                    for cycle in [1, 3, 5]:
                        for ambient_t in [20.0, 35.0, 45.0]:
                            res = accelerator.predict_cycle_performance(
                                steam_volume_cwe=steam_vol,
                                soak_days=soak,
                                injection_pressure=inj_p,
                                cycle_number=cycle,
                                producing_days=120,
                                spm=5.5,
                                ambient_temp_c=ambient_t
                            )
                            X.append([steam_vol, soak, inj_p, cycle, 120, 5.5, ambient_t])
                            y.append([res["cum_oil_bbl"], res["peak_oil_bopd"], res["cumulative_sor"], res["avg_oil_bopd"]])

        X = np.array(X)
        y = np.array(y)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        t0 = time.time()
        self.model.fit(X_train, y_train)
        self.train_time_sec = time.time() - t0
        
        # Validate surrogate
        t0 = time.time()
        y_pred = self.model.predict(X_test)
        self.inference_time_ms = (time.time() - t0) / len(X_test) * 1000.0

        # Calculate metrics for Cumulative Oil (first target)
        self.validation_metrics = baghewala_validation.compute_regression_metrics(y_test[:, 0], y_pred[:, 0])
        self.is_trained = True

    def predict(self, steam_volume_cwe: float, soak_days: float, injection_pressure: float,
                cycle_number: int = 1, producing_days: int = 120, spm: float = 5.5,
                ambient_temp_c: float = 30.0) -> Dict[str, Any]:
        """Predicts CSS metrics and provides ensemble-based uncertainty."""
        feat = np.array([[steam_volume_cwe, soak_days, injection_pressure, cycle_number, producing_days, spm, ambient_temp_c]])
        
        # Multi-tree prediction for uncertainty
        tree_preds = np.array([tree.predict(feat)[0] for tree in self.model.estimators_]) # (n_trees, n_outputs)
        
        mean_pred = np.mean(tree_preds, axis=0)
        uncertainty = np.std(tree_preds, axis=0) * 1.96 # 95% interval

        return {
            "cum_oil_bbl": float(mean_pred[0]),
            "cum_oil_bbl_uncertainty": float(uncertainty[0]),
            "peak_oil_bopd": float(mean_pred[1]),
            "peak_oil_bopd_uncertainty": float(uncertainty[1]),
            "cumulative_sor": float(mean_pred[2]),
            "cumulative_sor_uncertainty": float(uncertainty[2]),
            "avg_oil_bopd": float(mean_pred[3]),
            "avg_oil_bopd_uncertainty": float(uncertainty[3]),
            "inference_time_ms": self.inference_time_ms
        }

    def predict_cycle_performance(self, 
                                  steam_volume_cwe: float, 
                                  soak_days: float, 
                                  injection_pressure: float = 65.0,
                                  cycle_number: int = 1,
                                  producing_days: int = 120,
                                  spm: float = 5.5,
                                  ambient_temp_c: float = 30.0) -> Dict[str, Any]:
        """
        Backwards-compatible interface for cycle evaluation using physics accelerator.
        """
        accelerator = CSSPhysicsAccelerator(self.res_model)
        return accelerator.predict_cycle_performance(
            steam_volume_cwe=steam_volume_cwe,
            soak_days=soak_days,
            injection_pressure=injection_pressure,
            cycle_number=cycle_number,
            producing_days=producing_days,
            spm=spm,
            ambient_temp_c=ambient_temp_c
        )


# Aliases & Global Instances
baghewala_accelerator = CSSPhysicsAccelerator()
baghewala_surrogate = CSSRandomForestSurrogate()
