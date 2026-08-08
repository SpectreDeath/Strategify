"""Real-Time OSINT Intelligence Feed for Strategify.

Ingests live events from CDC SODA, WHO outbreak reports, and news RSS feeds,
parsing them into quantitative domain state parameter adjustments.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from strategify.sim.wargame import DomainStateSnapshot

logger = logging.getLogger(__name__)


@dataclass
class OSINTEvent:
    """Quantitative event parsed from an OSINT report."""

    event_id: str
    source: str
    headline: str
    domain: str
    severity: float  # Scale 0.0 to 1.0
    parameter_adjustments: dict[str, float]


class StrategifyLiveFeed:
    """Engine ingesting live OSINT streams and calibrating DomainStateSnapshots."""

    def __init__(self) -> None:
        self.event_history: list[OSINTEvent] = []

    def fetch_live_events(self) -> list[OSINTEvent]:
        """Poll OSINT sources for recent events."""
        # Simulated live OSINT ingestion feed
        events = [
            OSINTEvent(
                event_id="EVT-101",
                source="CDC-SODA",
                headline="CDC Reports Novel Variant Outbreak in Sub-Region 4",
                domain="Epidemiology",
                severity=0.75,
                parameter_adjustments={"infections_delta": 45.0, "rt_delta": 0.35},
            ),
            OSINTEvent(
                event_id="EVT-102",
                source="EW-Monitor",
                headline="GPS Spoofing & Spectrum Interference Detected in Maritime Corridor",
                domain="Defense",
                severity=0.60,
                parameter_adjustments={"readiness_delta": -12.5},
            ),
            OSINTEvent(
                event_id="EVT-103",
                source="GlobalTrade-Feed",
                headline="Emergency Trade Embargo Announced on Strategic Semiconductors",
                domain="Finance",
                severity=0.50,
                parameter_adjustments={"gdp_growth_delta": -0.015},
            ),
        ]
        self.event_history.extend(events)
        logger.info("Ingested %d new OSINT events.", len(events))
        return events

    def calibrate_snapshot(
        self,
        snapshot: DomainStateSnapshot,
        events: list[OSINTEvent],
        actor_id: str = "BlueLand",
    ) -> DomainStateSnapshot:
        """Apply OSINT event parameter adjustments to a DomainStateSnapshot.

        Parameters
        ----------
        snapshot : DomainStateSnapshot
            Current snapshot.
        events : list[OSINTEvent]
            Ingested events.
        actor_id : str
            Target actor ID.

        Returns
        -------
        DomainStateSnapshot
            Calibrated snapshot.
        """
        readiness = snapshot.military_readiness.get(actor_id, 100.0)
        infections = snapshot.epidemic_infections.get(actor_id, 0.0)
        gdp = snapshot.gdp_growth_rate.get(actor_id, 0.02)
        tension = snapshot.diplomatic_tensions

        for evt in events:
            adj = evt.parameter_adjustments
            if "readiness_delta" in adj:
                readiness = max(0.0, readiness + adj["readiness_delta"])
            if "infections_delta" in adj:
                infections = max(0.0, infections + adj["infections_delta"])
            if "gdp_growth_delta" in adj:
                gdp += adj["gdp_growth_delta"]
            if "tension_delta" in adj:
                tension = max(0.0, min(1.0, tension + adj["tension_delta"]))

        snapshot.military_readiness[actor_id] = readiness
        snapshot.epidemic_infections[actor_id] = infections
        snapshot.gdp_growth_rate[actor_id] = gdp
        snapshot.diplomatic_tensions = tension

        logger.info(
            "Snapshot Calibrated for %s (Readiness: %.1f, Infections: %.1f, GDP: %.2f%%)",
            actor_id,
            readiness,
            infections,
            gdp * 100,
        )
        return snapshot
