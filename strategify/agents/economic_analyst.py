"""Economic analysis capabilities for state actors.

This module provides economic forecasting, policy impact analysis, and cost-benefit
evaluation for StateActorAgent, following the pattern of IntelligenceComponent.

Classes:
- EconomicIndicator: Enum for economic metrics
- EconomicDataPoint: Time-series data structure
- EconomicForecast: Forecast results with confidence intervals
- PolicyImpact: Cost-benefit analysis results
- EconomicForecaster: Attached component for economic analysis
- EconomicAdvisor: Policy recommendation engine
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from strategify.agents.state_actor import StateActorAgent

logger = logging.getLogger(__name__)


class EconomicIndicator(Enum):
    """Types of economic indicators for forecasting."""

    GDP_GROWTH = "gdp_growth"
    INFLATION = "inflation"
    UNEMPLOYMENT = "unemployment"
    TRADE_BALANCE = "trade_balance"
    INDUSTRIAL_PRODUCTION = "industrial_production"
    CONSUMER_CONFIDENCE = "consumer_confidence"


class PolicyType(Enum):
    """Types of economic policies to analyze."""

    TARIFF = "tariff"
    SUBSIDY = "subsidy"
    TAX_CHANGE = "tax_change"
    REGULATION = "regulation"
    PUBLIC_SPENDING = "public_spending"
    SANCTION = "sanction"
    TRADE_AGREEMENT = "trade_agreement"


@dataclass
class EconomicDataPoint:
    """A single economic data point in a time series.

    Attributes
    ----------
    timestamp : float
        Unix timestamp of this data point.
    indicator : EconomicIndicator
        Type of indicator.
    value : float
        Numeric value.
    source : str
        Data source identifier.
    """

    timestamp: float
    indicator: EconomicIndicator
    value: float
    source: str


@dataclass
class EconomicForecast:
    """Results from an economic forecasting operation.

    Attributes
    ----------
    indicator : EconomicIndicator
        Indicator that was forecasted.
    horizon : int
        Number of steps ahead.
    predicted_value : float
        Point estimate.
    lower_bound : float
        Lower confidence bound.
    upper_bound : float
        Upper confidence bound.
    confidence : float
        Confidence level [0.0, 1.0]. Never 1.0.
    methodology : str
        Forecasting method used.
    timestamp : float
        Unix timestamp of forecast.
    """

    indicator: EconomicIndicator
    horizon: int
    predicted_value: float
    lower_bound: float
    upper_bound: float
    confidence: float
    methodology: str
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.confidence > 0.95:
            self.confidence = 0.95
        if self.confidence < 0.0:
            self.confidence = 0.0


@dataclass
class PolicyImpact:
    """Results from a policy impact analysis.

    Attributes
    ----------
    policy_type : PolicyType
        Type of policy analyzed.
    estimated_cost : float
        Estimated cost (negative = cost, positive = value).
    estimated_benefit : float
        Estimated benefit.
    net_impact : float
        Net impact (benefit - cost).
    affected_sectors : list[str]
        List of affected economic sectors.
    implementation_time : int
        Steps to implement.
    confidence : float
        Confidence in estimates [0.0, 1.0].
    risks : list[str]
        Identified risks.
    timestamp : float
        Unix timestamp of analysis.
    """

    policy_type: PolicyType
    estimated_cost: float
    estimated_benefit: float
    net_impact: float
    affected_sectors: list[str]
    implementation_time: int
    confidence: float
    risks: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.confidence > 0.95:
            self.confidence = 0.95
        if self.confidence < 0.0:
            self.confidence = 0.0
        if not self.risks:
            self._assess_default_risks()

    def _assess_default_risks(self) -> None:
        """Add default risk assessments based on policy type."""
        if self.policy_type == PolicyType.SANCTION:
            self.risks.append("Retaliation risk")
            self.risks.append("Trade disruption")
        elif self.policy_type == PolicyType.TARIFF:
            self.risks.append("Consumer price increase")
            self.risks.append("Retaliatory tariffs")
        elif self.policy_type == PolicyType.TAX_CHANGE:
            self.risks.append("Behavioral response")
            self.risks.append("Fiscal revenue impact")


class EconomicForecaster:
    """Attached to StateActorAgent for economic forecasting and analysis.

    Parameters
    ----------
    owner : StateActorAgent
        The agent that owns this component.
    """

    def __init__(self, owner: StateActorAgent) -> None:
        self.owner = owner
        self.forecasts: list[EconomicForecast] = []
        self.policy_impacts: list[PolicyImpact] = []
        self.historical_data: list[EconomicDataPoint] = []
        self.analysis_capability: float = 0.5

    def _get_trade_network(self):
        """Get the trade network from the model if available."""
        model = self.owner.model
        if hasattr(model, "trade_network") and model.trade_network is not None:
            return model.trade_network
        return None

    def forecast_indicator(
        self,
        indicator: EconomicIndicator,
        horizon: int = 3,
    ) -> EconomicForecast | None:
        """Forecast an economic indicator over a time horizon.

        Parameters
        ----------
        indicator : EconomicIndicator
            Indicator to forecast.
        horizon : int
            Number of steps ahead to forecast.

        Returns
        -------
        EconomicForecast | None
            Forecast results or None if forecasting failed.
        """
        trade_network = self._get_trade_network()

        if trade_network is None:
            return self._generate_synthetic_forecast(indicator, horizon)

        current_value = self._get_current_indicator_value(indicator, trade_network)

        noise = np.random.normal(0, 0.1)
        trend_factor = self.analysis_capability * 0.05

        predicted = current_value * (1 + trend_factor * horizon) + noise

        margin = 0.2 * horizon
        lower = predicted - margin
        upper = predicted + margin

        confidence = self.analysis_capability * 0.8

        forecast = EconomicForecast(
            indicator=indicator,
            horizon=horizon,
            predicted_value=predicted,
            lower_bound=lower,
            upper_bound=upper,
            confidence=confidence,
            methodology="moving_average",
        )

        self.forecasts.append(forecast)
        logger.debug(
            "Agent %s forecasted %s for horizon %d: %.2f (CI: %.2f-%.2f)",
            self.owner.region_id,
            indicator.value,
            horizon,
            predicted,
            lower,
            upper,
        )

        return forecast

    def _get_current_indicator_value(
        self,
        indicator: EconomicIndicator,
        trade_network,
    ) -> float:
        """Get the current value of an indicator from trade network."""
        econ_features = trade_network.get_economic_features(self.owner.unique_id)

        mapping = {
            EconomicIndicator.GDP_GROWTH: econ_features.get("gdp", 0.0) / 1e9,
            EconomicIndicator.TRADE_BALANCE: econ_features.get("trade_balance", 0.0),
            EconomicIndicator.INFLATION: 0.03,
            EconomicIndicator.UNEMPLOYMENT: 0.05,
            EconomicIndicator.INDUSTRIAL_PRODUCTION: 0.5,
            EconomicIndicator.CONSUMER_CONFIDENCE: 0.6,
        }

        return mapping.get(indicator, 0.0)

    def _generate_synthetic_forecast(
        self,
        indicator: EconomicIndicator,
        horizon: int,
    ) -> EconomicForecast:
        """Generate a synthetic forecast when no trade network available."""
        base_values = {
            EconomicIndicator.GDP_GROWTH: 0.02,
            EconomicIndicator.INFLATION: 0.03,
            EconomicIndicator.UNEMPLOYMENT: 0.05,
            EconomicIndicator.TRADE_BALANCE: 0.0,
            EconomicIndicator.INDUSTRIAL_PRODUCTION: 0.5,
            EconomicIndicator.CONSUMER_CONFIDENCE: 0.6,
        }

        base = base_values.get(indicator, 0.0)
        noise = np.random.normal(0, 0.05)
        predicted = base + noise

        margin = 0.15 * horizon
        confidence = 0.4

        return EconomicForecast(
            indicator=indicator,
            horizon=horizon,
            predicted_value=predicted,
            lower_bound=predicted - margin,
            upper_bound=predicted + margin,
            confidence=confidence,
            methodology="synthetic",
        )

    def analyze_policy_impact(self, policy_type: PolicyType) -> PolicyImpact:
        """Analyze the potential impact of an economic policy.

        Parameters
        ----------
        policy_type : PolicyType
            Type of policy to analyze.

        Returns
        -------
        PolicyImpact
            Analysis results.
        """
        trade_network = self._get_trade_network()

        econ_features = {}
        if trade_network:
            econ_features = trade_network.get_economic_features(self.owner.unique_id)

        gdp = econ_features.get("gdp", 1e10)
        trade_balance = econ_features.get("trade_balance", 0.0)
        cap = self.owner.capabilities.get("economic", 0.5)

        policy_profiles = {
            PolicyType.TARIFF: (
                gdp * 0.01 * cap,
                gdp * 0.005 * cap,
                2,
                ["imports", "consumer_prices"],
            ),
            PolicyType.SUBSIDY: (
                gdp * 0.02,
                gdp * 0.03,
                3,
                ["agriculture", "industry"],
            ),
            PolicyType.TAX_CHANGE: (
                gdp * 0.015,
                gdp * 0.02,
                4,
                ["government_revenue", "investment"],
            ),
            PolicyType.REGULATION: (
                gdp * 0.005,
                gdp * 0.01,
                6,
                ["business_compliance", "labor_market"],
            ),
            PolicyType.PUBLIC_SPENDING: (
                gdp * 0.03,
                gdp * 0.04,
                2,
                ["infrastructure", "services"],
            ),
            PolicyType.SANCTION: (
                abs(trade_balance) * 0.5 + gdp * 0.01,
                gdp * 0.005,
                1,
                ["exports", "diplomatic_relations"],
            ),
            PolicyType.TRADE_AGREEMENT: (
                gdp * 0.005,
                gdp * 0.02,
                5,
                ["trade_volume", "investment_flows"],
            ),
        }

        cost, benefit, impl_time, sectors = policy_profiles.get(
            policy_type,
            (gdp * 0.01, gdp * 0.01, 3, ["general"]),
        )

        net_impact = benefit - cost
        confidence = cap * 0.85

        impact = PolicyImpact(
            policy_type=policy_type,
            estimated_cost=cost,
            estimated_benefit=benefit,
            net_impact=net_impact,
            affected_sectors=sectors,
            implementation_time=impl_time,
            confidence=confidence,
        )

        self.policy_impacts.append(impact)
        logger.debug(
            "Agent %s analyzed %s policy: net impact %.2e",
            self.owner.region_id,
            policy_type.value,
            net_impact,
        )

        return impact

    def calculate_cost_benefit(
        self,
        proposal: dict[str, Any],
    ) -> PolicyImpact | None:
        """Calculate cost-benefit for a specific proposal.

        Parameters
        ----------
        proposal : dict
            Proposal containing policy details:
            - type: PolicyType value
            - scale: float (optional, defaults to 1.0)

        Returns
        -------
        PolicyImpact | None
            Cost-benefit analysis or None if proposal invalid.
        """
        policy_type_str = proposal.get("type", "")
        try:
            policy_type = PolicyType(policy_type_str)
        except ValueError:
            logger.warning(f"Invalid policy type: {policy_type_str}")
            return None

        scale = proposal.get("scale", 1.0)

        base_impact = self.analyze_policy_impact(policy_type)

        scaled_cost = base_impact.estimated_cost * scale
        scaled_benefit = base_impact.estimated_benefit * scale

        return PolicyImpact(
            policy_type=policy_type,
            estimated_cost=scaled_cost,
            estimated_benefit=scaled_benefit,
            net_impact=scaled_benefit - scaled_cost,
            affected_sectors=base_impact.affected_sectors,
            implementation_time=max(1, base_impact.implementation_time),
            confidence=base_impact.confidence,
            risks=base_impact.risks.copy(),
        )

    def get_market_trends(self) -> dict[str, Any]:
        """Identify current economic patterns and trends.

        Returns
        -------
        dict
            Market trend analysis including:
            - trend_direction: "expanding", "contracting", "stable"
            - key_indicators: dict of indicator values
            - risk_level: float [0.0, 1.0]
            - opportunities: list of identified opportunities
        """
        trade_network = self._get_trade_network()

        if trade_network:
            econ_features = trade_network.get_economic_features(self.owner.unique_id)
            trade_balance = econ_features.get("trade_balance", 0.0)
            gdp = econ_features.get("gdp", 1e10)
        else:
            trade_balance = 0.0
            gdp = 1e10

        if trade_balance > 0:
            trend_direction = "expanding"
        elif trade_balance < 0:
            trend_direction = "contracting"
        else:
            trend_direction = "stable"

        key_indicators = {
            "trade_balance": trade_balance,
            "gdp": gdp,
            "economic_capability": self.owner.capabilities.get("economic", 0.5),
        }

        risk_level = 0.5 - (self.analysis_capability * 0.3)
        if trade_balance < 0:
            risk_level += 0.2

        opportunities = []
        if trend_direction == "contracting":
            opportunities.append("export_subsidies")
            opportunities.append("trade_agreements")
        if self.owner.capabilities.get("economic", 0.5) > 0.7:
            opportunities.append("foreign_investment")

        return {
            "trend_direction": trend_direction,
            "key_indicators": key_indicators,
            "risk_level": min(1.0, max(0.0, risk_level)),
            "opportunities": opportunities,
        }

    def step(self) -> None:
        """Update economic analysis for the current step."""
        pass


class EconomicAdvisor:
    """Economic policy recommendation engine.

    Parameters
    ----------
    owner : StateActorAgent
        The agent that owns this advisor.
    """

    def __init__(self, owner: StateActorAgent) -> None:
        self.owner = owner
        self.forecaster = EconomicForecaster(owner)
        self.recommendations: list[dict[str, Any]] = []

    def recommend_trade_policy(self) -> dict[str, Any]:
        """Recommend optimal trade policy based on current conditions.

        Returns
        -------
        dict
            Recommendation including:
            - policy: "Open", "Protect", "Sanction"
            - confidence: float
            - reasoning: str
        """
        trade_network = self.forecaster._get_trade_network()

        if trade_network:
            econ_features = trade_network.get_economic_features(self.owner.unique_id)
            trade_balance = econ_features.get("trade_balance", 0.0)
        else:
            trade_balance = 0.0

        cap = self.owner.capabilities.get("economic", 0.5)

        if cap < 0.4:
            policy = "Open"
            reasoning = "Low capability - focus on comparative advantage"
        elif abs(trade_balance) < 0.1:
            policy = "Open"
            reasoning = "Balanced trade - pursue openness"
        elif trade_balance > 0:
            policy = "Open"
            reasoning = "Trade surplus - maintain openness for exports"
        else:
            policy = "Protect"
            reasoning = "Trade deficit - protect domestic industries"

        return {
            "policy": policy,
            "confidence": cap * 0.9,
            "reasoning": reasoning,
        }

    def advise_tariff_decision(self, target_region: str | None = None) -> dict[str, Any]:
        """Advise on tariff imposition.

        Parameters
        ----------
        target_region : str | None
            Region to potentially tariff (None = general).

        Returns
        -------
        dict
            Recommendation including:
            - decision: "Impose", "Maintain", "Remove"
            - rate: float (0.0-1.0)
            - confidence: float
            - reasoning: str
        """
        impact = self.forecaster.analyze_policy_impact(PolicyType.TARIFF)

        cap = self.owner.capabilities.get("economic", 0.5)

        if impact.net_impact > 0:
            decision = "Maintain" if cap > 0.5 else "Impose"
            reasoning = "Positive net impact from tariffs"
        else:
            decision = "Remove"
            reasoning = "Negative net impact from tariffs"

        return {
            "decision": decision,
            "rate": 0.1 * cap,
            "confidence": impact.confidence,
            "reasoning": reasoning,
        }

    def assess_sanction_effectiveness(self, target_id: int) -> dict[str, Any]:
        """Assess potential effectiveness of sanctions against a target.

        Parameters
        ----------
        target_id : int
            Agent ID to sanction.

        Returns
        -------
        dict
            Assessment including:
            - effective: bool
            - estimated_impact: float
            - confidence: float
            - risks: list[str]
        """
        model = self.owner.model
        target_agent = model._agent_registry.get(target_id)

        if target_agent is None:
            return {
                "effective": False,
                "estimated_impact": 0.0,
                "confidence": 0.0,
                "risks": ["Target not found"],
            }

        impact = self.forecaster.analyze_policy_impact(PolicyType.SANCTION)

        target_econ = target_agent.capabilities.get("economic", 0.5)

        effectiveness = max(0.0, 1.0 - target_econ) * impact.confidence

        risks = [
            "Economic retaliation",
            "Trade route disruption",
            "Allied cooperation required",
        ]

        if self.owner.capabilities.get("economic", 0.5) < target_econ:
            risks.append("Asymmetric economic capacity")

        return {
            "effective": effectiveness > 0.5,
            "estimated_impact": impact.net_impact * effectiveness,
            "confidence": impact.confidence,
            "risks": risks,
        }

    def step(self) -> None:
        """Update recommendations for the current step."""
        self.forecaster.step()

        rec = self.recommend_trade_policy()
        self.recommendations.append(rec)
