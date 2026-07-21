"""Tests for econometrics module."""

import numpy as np
import pytest

from strategify.economics.econometrics import (
    FiscalImpactCalculator,
    RegressionModel,
    SupplyDemandEquilibrium,
    TimeSeriesAnalyzer,
    TradeElasticityEstimator,
)


class TestRegressionModel:
    """Tests for RegressionModel."""

    def test_regression_fit_and_predict(self):
        np.random.seed(42)
        X = np.random.randn(50, 2)
        y = 2.5 * X[:, 0] - 1.2 * X[:, 1] + 3.0 + np.random.randn(50) * 0.1

        model = RegressionModel(n_features=2)
        result = model.fit(X, y)

        assert model.is_fitted is True
        assert abs(model.intercept - 3.0) < 0.5
        assert abs(model.coefficients[0] - 2.5) < 0.5
        assert result.r_squared > 0.9

        preds = model.predict(X[:5])
        assert len(preds) == 5

    def test_unfitted_predict_raises(self):
        model = RegressionModel(n_features=2)
        with pytest.raises(ValueError, match="Model not fitted"):
            model.predict(np.array([[1.0, 2.0]]))


class TestTimeSeriesAnalyzer:
    """Tests for TimeSeriesAnalyzer."""

    def test_time_series_forecast(self):
        series = [10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0]
        analyzer = TimeSeriesAnalyzer(lag=2)
        analyzer.fit(series)

        res = analyzer.forecast(horizon=3)
        assert len(res.forecast) == 3
        assert res.forecast[0] > 0.0

    def test_insufficient_data(self):
        analyzer = TimeSeriesAnalyzer(lag=2)
        analyzer.fit([1.0])
        res = analyzer.forecast(horizon=2)
        assert res.methodology == "insufficient_data"


class TestSupplyDemandEquilibrium:
    """Tests for SupplyDemandEquilibrium."""

    def test_calculate_equilibrium(self):
        eq = SupplyDemandEquilibrium(elasticity=-1.5)
        p_eq, q_eq = eq.find_equilibrium(
            supply_curve=np.array([10.0, 1.0]),
            demand_curve=np.array([100.0, -1.0]),
        )
        assert p_eq > 0.0
        assert q_eq > 0.0


class TestFiscalImpactCalculator:
    """Tests for FiscalImpactCalculator."""

    def test_fiscal_multiplier(self):
        calc = FiscalImpactCalculator(baseline_gdp=1e12)
        impact = calc.calculate_impact(spending=1_000_000.0, category="infrastructure")

        assert impact.multiplier == 1.8
        assert impact.total_impact == 1_800_000.0
        assert impact.gdp_impact > 0.0


class TestTradeElasticityEstimator:
    """Tests for TradeElasticityEstimator."""

    def test_estimate_elasticity(self):
        estimator = TradeElasticityEstimator()
        import_data = [(10.0, 100.0), (12.0, 80.0), (14.0, 60.0)]

        res = estimator.estimate_elasticity(import_data)
        assert res.elasticity < 0.0
