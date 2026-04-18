"""Econometric modeling and statistical analysis tools.

Provides statistical forecasting and market analysis capabilities:
- RegressionModel: Linear regression for economic data
- TimeSeriesAnalyzer: Time-series analysis and forecasting
- SupplyDemandEquilibrium: Market equilibrium analysis
- FiscalImpactCalculator: Government spending effects
- TradeElasticityEstimator: Import/export sensitivity analysis
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RegressionResult:
    """Results from a regression analysis."""

    coefficients: np.ndarray
    intercept: float
    r_squared: float
    standard_errors: np.ndarray
    p_values: np.ndarray
    residuals: np.ndarray


class RegressionModel:
    """Linear regression for economic data analysis.

    Parameters
    ----------
    n_features : int
        Number of independent variables.
    """

    def __init__(self, n_features: int) -> None:
        self.n_features = n_features
        self.coefficients: np.ndarray | None = None
        self.intercept: float = 0.0
        self.is_fitted: bool = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> RegressionResult:
        """Fit the regression model.

        Parameters
        ----------
        X : np.ndarray
            Feature matrix (n_samples, n_features).
        y : np.ndarray
            Target vector (n_samples,).

        Returns
        -------
        RegressionResult
            Fitting results.
        """
        n_samples, n_features = X.shape

        X_with_intercept = np.column_stack([np.ones(n_samples), X])

        try:
            beta = np.linalg.lstsq(X_with_intercept, y, rcond=None)[0]
        except np.linalg.LinAlgError:
            beta = np.zeros(n_features + 1)

        self.intercept = beta[0]
        self.coefficients = beta[1:]
        self.is_fitted = True

        y_pred = self.predict(X)
        residuals = y - y_pred

        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        mse = ss_res / max(1, n_samples - n_features - 1)
        var_beta = mse * np.linalg.inv(X_with_intercept.T @ X_with_intercept + 1e-6 * np.eye(n_features + 1))
        standard_errors = np.sqrt(np.diag(var_beta))
        p_values = np.array([self._calc_p_value(se, beta[i]) for i, se in enumerate(standard_errors)])

        result = RegressionResult(
            coefficients=self.coefficients,
            intercept=self.intercept,
            r_squared=r_squared,
            standard_errors=standard_errors[1:],
            p_values=p_values[1:],
            residuals=residuals,
        )

        return result

    def _calc_p_value(self, se: float, beta: float) -> float:
        """Calculate p-value from coefficient and standard error."""
        if se < 1e-10:
            return 0.0
        t_stat = beta / se
        try:
            from scipy import stats

            return 2 * (1 - stats.t.cdf(abs(t_stat), df=100))
        except ImportError:
            return 0.05 if abs(t_stat) > 1.96 else 0.5

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using fitted model.

        Parameters
        ----------
        X : np.ndarray
            Feature matrix.

        Returns
        -------
        np.ndarray
            Predictions.
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted")

        return X @ self.coefficients + self.intercept


@dataclass
class TimeSeriesResult:
    """Results from time-series analysis."""

    forecast: np.ndarray
    lower_bound: np.ndarray
    upper_bound: np.ndarray
    confidence: float
    methodology: str


class TimeSeriesAnalyzer:
    """Time-series analysis and ARIMA-style forecasting.

    Parameters
    ----------
    lag : int
        Number of lags to use.
    """

    def __init__(self, lag: int = 3) -> None:
        self.lag = lag
        self.history: list[float] = []

    def fit(self, series: list[float]) -> None:
        """Fit the analyzer to historical data.

        Parameters
        ----------
        series : list[float]
            Historical time series.
        """
        self.history = list(series)

    def forecast(self, horizon: int = 1, confidence: float = 0.95) -> TimeSeriesResult:
        """Generate forecast.

        Parameters
        ----------
        horizon : int
            Steps ahead to forecast.
        confidence : float
            Confidence level.

        Returns
        -------
        TimeSeriesResult
            Forecast results.
        """
        if len(self.history) < 2:
            return TimeSeriesResult(
                forecast=np.array([0.0] * horizon),
                lower_bound=np.array([0.0] * horizon),
                upper_bound=np.array([0.0] * horizon),
                confidence=0.5,
                methodology="insufficient_data",
            )

        values = np.array(self.history)

        if len(values) > self.lag:
            X = np.column_stack([values[i : i - self.lag] for i in range(self.lag, len(values))]).T
            y = values[self.lag :]

            if X.shape[0] > 0 and X.shape[1] > 0:
                try:
                    reg = RegressionModel(self.lag)
                    result = reg.fit(X, y)

                    last_lags = values[-self.lag :][::-1]
                    forecast = []
                    bounds = []

                    for h in range(horizon):
                        pred = reg.predict(last_lags.reshape(1, -1))[0]
                        se = np.std(result.residuals) if len(result.residuals) > 0 else 0.1

                        z_critical = 1.96 if confidence > 0.95 else 1.645
                        margin = z_critical * se * (1 + h * 0.1)

                        forecast.append(pred)
                        bounds.append(margin)

                    forecast = np.array(forecast)
                    lower = forecast - np.array(bounds)
                    upper = forecast + np.array(bounds)

                    return TimeSeriesResult(
                        forecast=forecast,
                        lower_bound=lower,
                        upper_bound=upper,
                        confidence=confidence,
                        methodology="arima",
                    )
                except Exception:
                    pass

        mean = np.mean(values)
        std = np.std(values)

        forecast = np.full(horizon, mean)
        z_critical = 1.96 if confidence > 0.95 else 1.645
        margin = z_critical * std

        lower_bound = forecast - margin
        upper_bound = forecast + margin

        return TimeSeriesResult(
            forecast=forecast,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            confidence=0.6,
            methodology="moving_average",
        )


class SupplyDemandEquilibrium:
    """Market supply-demand equilibrium analysis.

    Parameters
    ----------
    price弹性 : float
        Price elasticity of demand.
    """

    def __init__(self, elasticity: float = -1.0) -> None:
        self.elasticity = elasticity

    def find_equilibrium(
        self,
        supply_curve: np.ndarray,
        demand_curve: np.ndarray,
    ) -> tuple[float, float]:
        """Find market equilibrium price and quantity.

        Parameters
        ----------
        supply_curve : np.ndarray
            Supply as function of quantity [intercept, slope].
        demand_curve : np.ndarray
            Demand as function of quantity [intercept, slope].

        Returns
        -------
        tuple[float, float]
            Equilibrium (price, quantity).
        """
        s_intercept, s_slope = supply_curve
        d_intercept, d_slope = demand_curve

        if abs(d_slope - s_slope) < 1e-6:
            return (d_intercept / 2, 0.0)

        q_eq = (s_intercept - d_intercept) / (d_slope - s_slope)
        p_eq = s_intercept + s_slope * q_eq

        return (p_eq, max(0.0, q_eq))

    def calculate_consumer_surplus(self, p: float, demand_curve: np.ndarray) -> float:
        """Calculate consumer surplus.

        Parameters
        ----------
        p : float
            Equilibrium price.
        demand_curve : np.ndarray
            Demand curve parameters.

        Returns
        -------
        float
            Consumer surplus.
        """
        d_intercept, d_slope = demand_curve
        if d_slope >= 0:
            return 0.0

        q_max = -d_intercept / d_slope
        return 0.5 * (q_max - 0) * (d_intercept - p)

    def calculate_producer_surplus(self, p: float, supply_curve: np.ndarray) -> float:
        """Calculate producer surplus.

        Parameters
        ----------
        p : float
            Equilibrium price.
        supply_curve : np.ndarray
            Supply curve parameters.

        Returns
        -------
        float
            Producer surplus.
        """
        s_intercept, s_slope = supply_curve
        if s_slope <= 0:
            return 0.0

        q_eq = (p - s_intercept) / s_slope
        return 0.5 * q_eq * (p - s_intercept)


@dataclass
class FiscalImpact:
    """Government spending impact analysis."""

    total_impact: float
    gdp_impact: float
    employment_impact: float
    inflation_impact: float
    multiplier: float


class FiscalImpactCalculator:
    """Government spending effects analysis.

    Parameters
    ----------
    baseline_gdp : float
        Baseline GDP for scaling.
    """

    def __init__(self, baseline_gdp: float = 1e12) -> None:
        self.baseline_gdp = baseline_gdp

    def calculate_impact(
        self,
        spending: float,
        category: str = "infrastructure",
    ) -> FiscalImpact:
        """Calculate fiscal multiplier impact.

        Parameters
        ----------
        spending : float
            Government spending amount.
        category : str
            Spending category.

        Returns
        -------
        FiscalImpact
            Impact analysis.
        """
        multipliers = {
            "infrastructure": 1.8,
            "defense": 1.2,
            "healthcare": 1.5,
            "education": 1.6,
            "welfare": 1.3,
            "tax_cut": 0.9,
        }

        multiplier = multipliers.get(category, 1.0)

        total_impact = spending * multiplier
        gdp_impact = total_impact / self.baseline_gdp

        employment_impact = total_impact / (50000.0)

        inflation_impact = 0.0
        if total_impact > 0.1 * self.baseline_gdp:
            inflation_impact = 0.02

        return FiscalImpact(
            total_impact=total_impact,
            gdp_impact=gdp_impact,
            employment_impact=employment_impact,
            inflation_impact=inflation_impact,
            multiplier=multiplier,
        )


@dataclass
class ElasticityEstimate:
    """Trade elasticity estimation result."""

    elasticity: float
    standard_error: float
    confidence_interval: tuple[float, float]
    p_value: float


class TradeElasticityEstimator:
    """Import/export sensitivity analysis.

    Parameters
    ----------
    trade_data : list[tuple[float, float]]
        List of (price, quantity) observations.
    """

    def __init__(self, trade_data: list[tuple[float, float]] | None = None) -> None:
        self.trade_data = trade_data or []

    def estimate_elasticity(
        self,
        import_data: list[tuple[float, float]] | None = None,
    ) -> ElasticityEstimate:
        """Estimate price elasticity of demand.

        Parameters
        ----------
        import_data : list[tuple[float, float]]
            (price, quantity) pairs.

        Returns
        -------
        ElasticityEstimate
            Elasticity estimate with confidence interval.
        """
        data = import_data or self.trade_data

        if len(data) < 2:
            return ElasticityEstimate(
                elasticity=-1.0,
                standard_error=0.5,
                confidence_interval=(-2.0, 0.0),
                p_value=0.5,
            )

        try:
            prices = np.array([d[0] for d in data])
            quantities = np.array([d[1] for d in data])

            log_p = np.log(np.maximum(prices, 1e-6))
            log_q = np.log(np.maximum(quantities, 1e-6))

            reg = RegressionModel(1)
            result = reg.fit(log_p.reshape(-1, 1), log_q)

            elasticity = result.coefficients[0] if result.coefficients is not None else -1.0
            se = result.standard_errors[0] if len(result.standard_errors) > 0 else 0.5
            p_val = result.p_values[0] if len(result.p_values) > 0 else 0.5

            z = 1.96
            ci_lower = elasticity - z * se
            ci_upper = elasticity + z * se

            return ElasticityEstimate(
                elasticity=elasticity,
                standard_error=se,
                confidence_interval=(ci_lower, ci_upper),
                p_value=p_val,
            )

        except Exception as e:
            logger.debug(f"Elasticity estimation failed: {e}")
            return ElasticityEstimate(
                elasticity=-1.0,
                standard_error=0.5,
                confidence_interval=(-2.0, 0.0),
                p_value=0.5,
            )
