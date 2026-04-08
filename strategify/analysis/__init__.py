"""Analysis tools: time series, causal inference, communities, sensitivity,
optimization, comparison, alerts, calibration, forecasting, counterfactuals,
and strategic analysis."""

from strategify.analysis.alerts import (
    AlertLevel,
    detect_contagion_spread,
    detect_escalation_spikes,
    detect_trend_reversals,
    run_early_warning,
)
from strategify.analysis.alliance_forecast import (
    AllianceStability,
    compute_alliance_strength,
    compute_network_resilience,
    forecast_alliance_stability,
    identify_vulnerable_alliances,
    predict_fracture_probability,
    suggest_rebalancing,
)
from strategify.analysis.calibration import (
    calibrate_parameters,
    compute_calibration_error,
    create_sample_historical_data,
    load_historical_crisis,
)
from strategify.analysis.causal import (
    build_causal_data,
    estimate_escalation_effect,
    pairwise_causal_effects,
)
from strategify.analysis.communities import (
    detect_communities,
    detect_communities_over_time,
    find_agent_community,
)
from strategify.analysis.comparison import (
    collect_trajectories,
    compare_trajectories,
    extract_trajectory,
    multi_scenario_comparison,
    trajectory_to_dataframe,
)
from strategify.analysis.counterfactual import (
    apply_intervention,
    compare_counterfactual,
    run_baseline,
    run_counterfactual,
    systematic_counterfactuals,
)
from strategify.analysis.forecasting import (
    compute_forecast_confidence,
    detect_forecast_escalation,
    forecast_all_regions,
    forecast_arima,
)
from strategify.analysis.leverage import (
    AgentLeverage,
    LeverageAlertLevel,
    LeverageAnalyzer,
    LeverageHistory,
    LeverageScore,
    LeverageType,
    compare_leverage_types,
    compute_leverage,
    compute_leverage_volatility,
    detect_leverage_anomalies,
    detect_leverage_regime_change,
    detect_leverage_shift,
    sensitivity_analysis,
    track_leverage,
)
from strategify.analysis.optimization import GeopolResourceProblem, optimize_resources
from strategify.analysis.sensitivity import rank_parameters, run_sensitivity_analysis
from strategify.analysis.strategic_risk import (
    RiskLevel,
    assess_all_risks,
    compute_regional_risk_matrix,
    compute_threat_score,
    compute_volatility,
    get_risk_level,
    identify_critical_regions,
)
from strategify.analysis.strategy_recommend import (
    StrategicRecommendation,
    StrategyReport,
    analyze_strategic_position,
    compute_optimal_action,
    compute_win_probability,
    generate_strategy_report,
    recommend_preemptive_actions,
)
from strategify.analysis.timeseries import (
    fit_var_model,
    granger_causality_test,
    pairwise_granger_causality,
    prepare_agent_timeseries,
)
from strategify.analysis.war_game import (
    AdversaryScenario,
    AdversaryType,
    WarGameResult,
    analyze_red_lines,
    predict_adversary_response,
    run_war_game,
    simulate_counter_strategy,
)

__all__ = [
    # Time series
    "prepare_agent_timeseries",
    "fit_var_model",
    "granger_causality_test",
    "pairwise_granger_causality",
    # Causal
    "build_causal_data",
    "estimate_escalation_effect",
    "pairwise_causal_effects",
    # Communities
    "detect_communities",
    "detect_communities_over_time",
    "find_agent_community",
    # Sensitivity
    "run_sensitivity_analysis",
    "rank_parameters",
    # Optimization
    "optimize_resources",
    "GeopolResourceProblem",
    # Comparison
    "extract_trajectory",
    "collect_trajectories",
    "compare_trajectories",
    "multi_scenario_comparison",
    "trajectory_to_dataframe",
    # Alerts
    "AlertLevel",
    "detect_escalation_spikes",
    "detect_trend_reversals",
    "detect_contagion_spread",
    "run_early_warning",
    # Calibration
    "load_historical_crisis",
    "compute_calibration_error",
    "calibrate_parameters",
    "create_sample_historical_data",
    # Forecasting
    "forecast_arima",
    "forecast_all_regions",
    "compute_forecast_confidence",
    "detect_forecast_escalation",
    # Counterfactual
    "run_baseline",
    "apply_intervention",
    "run_counterfactual",
    "compare_counterfactual",
    "systematic_counterfactuals",
    # Strategic Risk
    "RiskLevel",
    "compute_threat_score",
    "compute_volatility",
    "get_risk_level",
    "assess_all_risks",
    "identify_critical_regions",
    "compute_regional_risk_matrix",
    # War Game
    "AdversaryType",
    "AdversaryScenario",
    "WarGameResult",
    "predict_adversary_response",
    "run_war_game",
    "simulate_counter_strategy",
    "analyze_red_lines",
    # Alliance Forecast
    "AllianceStability",
    "compute_alliance_strength",
    "predict_fracture_probability",
    "forecast_alliance_stability",
    "identify_vulnerable_alliances",
    "compute_network_resilience",
    "suggest_rebalancing",
    # Strategy Recommendations
    "StrategicRecommendation",
    "StrategyReport",
    "analyze_strategic_position",
    "compute_optimal_action",
    "generate_strategy_report",
    "recommend_preemptive_actions",
    "compute_win_probability",
    # Leverage Analysis
    "LeverageType",
    "LeverageScore",
    "AgentLeverage",
    "LeverageAnalyzer",
    "LeverageHistory",
    "LeverageAlertLevel",
    "compute_leverage",
    "track_leverage",
    "detect_leverage_anomalies",
    "detect_leverage_shift",
    "detect_leverage_regime_change",
    "detect_leverage_shift",
    "compute_leverage_volatility",
    "sensitivity_analysis",
    "compare_leverage_types",
]
