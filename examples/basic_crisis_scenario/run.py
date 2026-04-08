"""Headless crisis scenario: runs 20 steps and dumps results to CSV."""

from __future__ import annotations

from pathlib import Path

from strategify.config.settings import DEFAULT_N_STEPS as N_STEPS
from strategify.sim.model import GeopolModel

model = GeopolModel()
for _ in range(N_STEPS):
    model.step()

df = model.datacollector.get_agent_vars_dataframe()
print(df.to_string())

output_path = Path(__file__).parent / "crisis_scenario_output.csv"
df.to_csv(output_path, index=True)
print(f"\nOutput written to: {output_path}")
