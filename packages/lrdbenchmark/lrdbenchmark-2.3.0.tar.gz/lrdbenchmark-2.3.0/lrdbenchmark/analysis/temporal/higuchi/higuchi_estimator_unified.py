"""Unified Higuchi estimator with backward-compatible API."""

from __future__ import annotations

import math
import warnings
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy import stats

from lrdbenchmark.models.estimators.base_estimator import BaseEstimator


class HiguchiEstimator(BaseEstimator):
    """Estimate fractal dimension and Hurst exponent using the Higuchi method."""

    def __init__(
        self,
        min_k: int = 2,
        max_k: Optional[int] = None,
        k_values: Optional[List[int]] = None,
        use_optimization: str = "auto",
    ) -> None:
        param_dict = {
            "min_k": int(min_k),
            "max_k": int(max_k) if max_k is not None else None,
            "k_values": [int(k) for k in k_values] if k_values is not None else None,
            "use_optimization": use_optimization,
        }

        super().__init__(**param_dict)
        self.parameters = param_dict

        self.optimization_framework = "numpy"

        self.k_values: List[int] = []
        self.l_values: List[float] = []
        self.estimated_hurst: Optional[float] = None
        self.fractal_dimension: Optional[float] = None
        self.confidence_interval: Optional[Dict[str, Tuple[float, float]]] = None
        self.r_squared: Optional[float] = None
        self.results: Dict[str, Any] = {}

        self._validate_parameters()

    # ------------------------------------------------------------------
    # Validation and parameter helpers
    # ------------------------------------------------------------------

    def _validate_parameters(self) -> None:
        if self.parameters["min_k"] < 2:
            raise ValueError("min_k must be at least 2")

        max_k = self.parameters["max_k"]
        if max_k is not None and max_k <= self.parameters["min_k"]:
            raise ValueError("max_k must be greater than min_k")

        if self.parameters["k_values"] is not None:
            k_array = np.asarray(self.parameters["k_values"], dtype=int)
            if np.any(k_array < 2):
                raise ValueError("All k values must be at least 2")
            if np.any(np.diff(k_array) <= 0):
                raise ValueError("k values must be in ascending order")

    # ------------------------------------------------------------------
    # Core estimation logic
    # ------------------------------------------------------------------

    def estimate(self, data: Union[np.ndarray, List[float]]) -> Dict[str, Any]:
        series = np.asarray(data, dtype=float)
        n = len(series)

        if n < 10:
            raise ValueError("Data length must be at least 10")

        k_values = self._determine_k_values(n)
        if len(k_values) < 3:
            raise ValueError("Need at least 3 k values")

        mean_centered = series - np.mean(series)
        cumulative = np.cumsum(mean_centered)

        curve_lengths = np.array(
            [self._calculate_curve_length_higuchi(cumulative, k) for k in k_values],
            dtype=float,
        )

        S_values = (n - 1) * curve_lengths / (k_values.astype(float) ** 2)

        valid_mask = np.isfinite(S_values) & (S_values > 0)
        valid_k = k_values[valid_mask]
        valid_S = S_values[valid_mask]
        valid_lengths = curve_lengths[valid_mask]

        if len(valid_S) < 3:
            raise ValueError("Need at least 3 k values")

        log_k = np.log(valid_k.astype(float))
        log_S = np.log(valid_S.astype(float))

        slope, intercept, r_value, p_value, std_err = stats.linregress(log_k, log_S)

        hurst_parameter = slope + 2.0
        fractal_dimension = 2.0 - hurst_parameter

        fractal_dimension = float(np.clip(fractal_dimension, 1.0, 2.0))
        hurst_parameter = float(np.clip(hurst_parameter, 0.0, 1.0))

        n_points = len(valid_S)
        t_value = stats.t.ppf(0.975, n_points - 2)
        ci_half_width = t_value * std_err

        confidence_interval = {
            "hurst_parameter": (hurst_parameter - ci_half_width, hurst_parameter + ci_half_width),
            "fractal_dimension": (fractal_dimension - ci_half_width, fractal_dimension + ci_half_width),
        }

        self.k_values = valid_k.tolist()
        self.l_values = valid_lengths.tolist()
        self.estimated_hurst = hurst_parameter
        self.fractal_dimension = fractal_dimension
        self.r_squared = r_value**2
        self.confidence_interval = confidence_interval

        self.results = {
            "hurst_parameter": hurst_parameter,
            "fractal_dimension": fractal_dimension,
            "confidence_interval": confidence_interval,
            "r_squared": float(self.r_squared),
            "p_value": float(p_value),
            "std_error": float(std_err),
            "slope": float(slope),
            "intercept": float(intercept),
            "k_values": self.k_values,
            "curve_lengths": self.l_values,
            "log_k_values": log_k.tolist(),
            "log_curve_lengths": np.log(valid_lengths).tolist(),
            "method": "higuchi_numpy",
            "optimization_framework": self.optimization_framework,
        }

        return self.results

    def _determine_k_values(self, n: int) -> np.ndarray:
        if self.parameters["k_values"] is not None:
            k_values = np.asarray(self.parameters["k_values"], dtype=int)
        elif self.parameters["max_k"] is not None:
            max_k = min(int(self.parameters["max_k"]), n // 2)
            k_values = np.arange(self.parameters["min_k"], max_k + 1, dtype=int)
        else:
            k_values = self._generate_default_k_values(n)

        k_values = k_values[k_values >= self.parameters["min_k"]]
        k_values = k_values[k_values < n // 2]
        return k_values.astype(int)

    def _generate_default_k_values(self, n: int) -> np.ndarray:
        values: List[int] = []
        for idx in range(1, 11):
            m = idx if idx <= 4 else int(2 ** ((idx + 5) / 4))
            if m >= n // 2:
                break
            values.append(m)
        return np.array(values, dtype=int)

    def _calculate_curve_length_higuchi(self, cumulative: np.ndarray, k: int) -> float:
        n = len(cumulative)
        if k >= n:
            return np.nan

        num_segments = n // k
        if num_segments < 2:
            return np.nan

        total_length = 0.0
        valid_segments = 0

        for i in range(1, num_segments):
            segment_length = 0.0
            segment_count = 0
            start_idx = (i - 1) * k
            end_idx = i * k

            for j in range(start_idx, end_idx):
                nxt = j + k
                if nxt < n:
                    segment_length += abs(cumulative[nxt] - cumulative[j])
                    segment_count += 1

            if segment_count > 0:
                total_length += segment_length / segment_count
                valid_segments += 1

        if valid_segments == 0:
            return np.nan

        return total_length / valid_segments

    # ------------------------------------------------------------------
    # Backward-compatible helpers
    # ------------------------------------------------------------------

    def _calculate_curve_length(self, data: Union[np.ndarray, List[float]], k: int) -> float:
        series = np.asarray(data, dtype=float)
        cumulative = np.cumsum(series - np.mean(series))
        length = self._calculate_curve_length_higuchi(cumulative, int(k))
        if not np.isfinite(length) or length <= 0:
            raise ValueError("No valid curve lengths calculated")
        return float(length)

    def get_confidence_intervals(self, confidence_level: float = 0.95) -> Dict[str, Tuple[float, float]]:
        if not self.results:
            raise ValueError("No estimation results available")

        std_err = self.results["std_error"]
        n_points = len(self.results["k_values"])
        t_value = stats.t.ppf((1 + confidence_level) / 2.0, n_points - 2)

        hurst = self.results["hurst_parameter"]
        fractal = self.results["fractal_dimension"]

        ci_hurst = (hurst - t_value * std_err, hurst + t_value * std_err)
        ci_fractal = (fractal - t_value * std_err, fractal + t_value * std_err)

        return {
            "hurst_parameter": (float(ci_hurst[0]), float(ci_hurst[1])),
            "fractal_dimension": (float(ci_fractal[0]), float(ci_fractal[1])),
        }

    def get_estimation_quality(self) -> Dict[str, Any]:
        if not self.results:
            raise ValueError("No estimation results available")

        return {
            "r_squared": self.results["r_squared"],
            "p_value": self.results["p_value"],
            "std_error": self.results["std_error"],
            "n_k_values": len(self.results["k_values"]),
        }

    def get_optimization_info(self) -> Dict[str, Any]:
        return {
            "current_framework": self.optimization_framework,
            "jax_available": False,
            "numba_available": False,
            "recommended_framework": "numpy",
        }

    # ------------------------------------------------------------------
    # Plotting helpers
    # ------------------------------------------------------------------

    def plot_scaling(self, **kwargs) -> None:
        if not self.results:
            raise ValueError("No estimation results available")

        self.plot_results(**kwargs)

    def plot_results(self, save_path: Optional[str] = None) -> None:
        try:
            import matplotlib.pyplot as plt

            if not self.results:
                raise ValueError("No estimation results available")

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

            ax1.loglog(self.k_values, self.l_values, "o-", linewidth=2, markersize=6)
            ax1.set_xlabel("k")
            ax1.set_ylabel("L(k)")
            ax1.set_title("Higuchi Curve Lengths")
            ax1.grid(True, alpha=0.3)

            log_k = np.array(self.results["log_k_values"])
            log_L = np.array(self.results["log_curve_lengths"])
            ax2.plot(log_k, log_L, "o", label="Data")

            slope = self.results["slope"]
            intercept = self.results["intercept"]
            x_line = np.linspace(min(log_k), max(log_k), 100)
            y_line = slope * x_line + intercept
            ax2.plot(x_line, y_line, "r--", label=f"D = {self.fractal_dimension:.3f}")
            ax2.set_xlabel("log(k)")
            ax2.set_ylabel("log(L(k))")
            ax2.set_title("Log-Log Regression")
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches="tight")
            else:
                plt.show()
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Matplotlib not available for plotting") from exc
