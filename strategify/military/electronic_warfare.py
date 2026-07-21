"""Electronic Warfare and Cyber-EM (CEMA) simulation.

This module provides:
- ElectronicWarfareSystem: Jamming, ECM, electronic attack/defense
- EMSpectrumManager: Frequency allocation, signal classification
- CyberOperation: Offensive and defensive cyber operations

SOC Code: 55-4010 (Cyber Operations)
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class ElectronicAttackType(Enum):
    """Types of electronic attack."""

    JAMMING = "jamming"
    DECEPTION = "deception"
    ELECTROMAGNETIC_PULSE = "emp"
    ANTIRADIATION = "anti_radiation"


class JammingTechnique(Enum):
    """Jamming modulation techniques."""

    NOISE = "noise"
    BARRAGE = "barrage"
    SPOT = "spot"
    SWEEP = "sweep"
    PULSE = "pulse"


class CyberOperationType(Enum):
    """Types of cyber operations."""

    RECON = "recon"
    EXPLOIT = "exploit"
    DENIAL = "denial"
    DESTRUCTION = "destruction"


class OperationStatus(Enum):
    """Status of EW or cyber operation."""

    PLANNING = "planning"
    ACTIVE = "active"
    SUCCESS = "success"
    FAILURE = "failure"
    DETECTED = "detected"


@dataclass
class ElectromagneticEffect:
    """An EM effect on a target."""

    effect_type: str
    target_id: str
    frequency_mhz: float
    effectiveness: float
    duration_seconds: float
    status: OperationStatus = OperationStatus.PLANNING


class ElectronicWarfareSystem:
    """Electronic warfare capabilities for an agent.

    Attributes
    ----------
    owner_id : str
        Agent that owns this system.
    jamming_capability : float
        Jamming effectiveness [0.0, 1.0].
    ecm_capability : float
        Electronic counter-measures [0.0, 1.0].
    emission_control : bool
        Whether emissions are controlled.
    """

    def __init__(self, owner_id: str) -> None:
        self.owner_id = owner_id
        self.jamming_capability: float = 0.5
        self.ecm_capability: float = 0.5
        self.emission_control: bool = False
        self.active_effects: list[ElectromagneticEffect] = []
        self.frequency_bands: dict[str, float] = {
            "VHF": 30.0,
            "UHF": 300.0,
            "L": 2000.0,
            "S": 4000.0,
            "C": 8000.0,
            "X": 12000.0,
        }

    def perform_jamming(
        self,
        target_id: str,
        technique: JammingTechnique,
        target_frequency: float,
        duration: float,
    ) -> ElectromagneticEffect:
        """Perform jamming operation.

        Parameters
        ----------
        target_id : str
            Target to jam.
        technique : JammingTechnique
            Jamming technique.
        target_frequency : float
            Target frequency in MHz.
        duration : float
            Duration in seconds.

        Returns
        -------
        ElectromagneticEffect
            Result of jamming operation.
        """
        effectiveness = self._calculate_jamming_effectiveness(technique, target_frequency)

        effect = ElectromagneticEffect(
            effect_type=ElectronicAttackType.JAMMING.value,
            target_id=target_id,
            frequency_mhz=target_frequency,
            effectiveness=effectiveness,
            duration_seconds=duration,
            status=OperationStatus.ACTIVE,
        )

        self.active_effects.append(effect)
        logger.info(
            "EW: Agent %s performing %s jamming on %s at %.1f MHz",
            self.owner_id,
            technique.value,
            target_id,
            target_frequency,
        )

        return effect

    def _calculate_jamming_effectiveness(
        self,
        technique: JammingTechnique,
        target_frequency: float,
    ) -> float:
        """Calculate jamming effectiveness."""
        base_effectiveness = self.jamming_capability

        if technique == JammingTechnique.NOISE:
            freq_factor = 0.8
        elif technique == JammingTechnique.BARRAGE:
            freq_factor = 0.6
        elif technique == JammingTechnique.SPOT:
            freq_factor = 0.9
        elif technique == JammingTechnique.SWEEP:
            freq_factor = 0.7
        else:
            freq_factor = 0.5

        band_penalty = 0.0
        for _band, max_freq in self.frequency_bands.items():
            if target_frequency < max_freq:
                band_penalty = 0.1
                break

        return max(0.1, base_effectiveness * freq_factor - band_penalty)

    def activate_ecm(self, threat_type: str) -> dict[str, Any]:
        """Activate electronic counter-measures.

        Parameters
        ----------
        threat_type : str
            Type of threat (radar, missile, etc).

        Returns
        -------
        dict
            ECM activation status.
        """
        effectiveness = self.ecm_capability * random.uniform(0.8, 1.2)
        effectiveness = min(1.0, effectiveness)

        response = {
            "ecm_activated": True,
            "threat_type": threat_type,
            "effectiveness": effectiveness,
            "techniques_used": [],
        }

        if threat_type == "radar":
            response["techniques_used"].append("chaff")
            response["techniques_used"].append("jamming")
        elif threat_type == "missile":
            response["techniques_used"].append("infrared_decoy")
            response["techniques_used"].append("stealth")

        logger.debug(
            "EW: Agent %s activated ECM against %s (effectiveness: %.2f)",
            self.owner_id,
            threat_type,
            effectiveness,
        )

        return response

    def emit_pulse(self, power: float, frequency: float) -> dict[str, Any]:
        """Emit an electromagnetic pulse.

        Parameters
        ----------
        power : float
            Pulse power in watts.
        frequency : float
            Frequency in MHz.

        Returns
        -------
        dict
            Pulse characteristics.
        """
        if self.emission_control:
            logger.warning(
                "EW: Agent %s attempted emission with emission control active",
                self.owner_id,
            )
            return {"success": False, "reason": "emission_control_active"}

        range_km = (power / frequency) * 0.1

        return {
            "success": True,
            "power": power,
            "frequency": frequency,
            "effective_range_km": range_km,
        }

    def step(self, dt: float) -> None:
        """Process EW system for time step."""
        for effect in self.active_effects:
            effect.duration_seconds -= dt
            if effect.duration_seconds <= 0:
                effect.status = OperationStatus.SUCCESS

        self.active_effects = [e for e in self.active_effects if e.status != OperationStatus.SUCCESS]


def calculate_path_loss(distance_km: float, frequency_mhz: float) -> float:
    """Calculate Free-Space Path Loss (FSPL) in dB.

    FSPL (dB) = 20*log10(d_km) + 20*log10(f_MHz) + 32.44
    """
    import math

    d = max(0.001, distance_km)
    f = max(1.0, frequency_mhz)
    return 20.0 * math.log10(d) + 20.0 * math.log10(f) + 32.44


class EMSpectrumManager:
    """Manage electromagnetic spectrum allocation and monitoring."""

    def __init__(self, owner_id: str) -> None:
        self.owner_id = owner_id
        self.allocated_frequencies: dict[str, list[float]] = {}
        self.detected_signals: list[dict] = []
        self.spectrum_occupancy: dict[float, float] = {}

    def allocate_frequency(
        self,
        system: str,
        frequency: float,
        bandwidth: float,
    ) -> dict[str, Any]:
        """Allocate a frequency band to a system."""
        if system not in self.allocated_frequencies:
            self.allocated_frequencies[system] = []

        conflicts = self._check_frequency_conflict(frequency, bandwidth)

        if conflicts:
            alternative = self._find_alternative_frequency(bandwidth)
            return {
                "allocated": False,
                "reason": "conflict",
                "alternative": alternative,
            }

        self.allocated_frequencies[system].append(frequency)

        return {
            "allocated": True,
            "frequency": frequency,
            "bandwidth": bandwidth,
        }

    def _check_frequency_conflict(
        self,
        frequency: float,
        bandwidth: float,
    ) -> list[str]:
        """Check for frequency conflicts."""
        conflicts = []

        for system, freqs in self.allocated_frequencies.items():
            for f in freqs:
                if abs(f - frequency) < bandwidth:
                    conflicts.append(system)

        return conflicts

    def _find_alternative_frequency(self, bandwidth: float) -> float:
        """Find an alternative frequency."""
        for freq in np.arange(30.0, 12000.0, bandwidth):
            if not self._check_frequency_conflict(freq, bandwidth):
                return freq

        return 225.0

    def detect_signal(
        self,
        source_id: str,
        frequency: float,
        signal_strength: float,
        distance_km: float = 1.0,
    ) -> dict[str, Any]:
        """Detect and classify an electromagnetic signal with path loss attenuation.

        Parameters
        ----------
        source_id : str
            Source of signal.
        frequency : float
            Signal frequency in MHz.
        signal_strength : float
            Signal strength [0.0, 1.0].
        distance_km : float
            Distance to source in km.

        Returns
        -------
        dict
            Signal classification.
        """
        path_loss_db = calculate_path_loss(distance_km, frequency)
        attenuated_strength = max(0.01, min(1.0, signal_strength / (1.0 + path_loss_db / 100.0)))
        signal_type = self._classify_signal(frequency, attenuated_strength)

        signal = {
            "source_id": source_id,
            "frequency": frequency,
            "strength": attenuated_strength,
            "path_loss_db": path_loss_db,
            "type": signal_type,
            "classification": self._determine_classification(signal_type),
        }

        self.detected_signals.append(signal)

        return signal

    def _classify_signal(self, frequency: float, strength: float) -> str:
        """Classify signal type based on characteristics."""
        if frequency < 300.0:
            if strength > 0.7:
                return "radar_vhf"
            return "communication_vhf"
        elif frequency < 2000.0:
            return "radar_l"
        elif frequency < 4000.0:
            return "radar_s"
        elif frequency < 8000.0:
            return "radar_c"
        elif frequency < 12000.0:
            return "radar_x"
        else:
            return "unknown"

    def _determine_classification(self, signal_type: str) -> str:
        """Determine classification level."""
        if "radar" in signal_type:
            return "military_hostile"
        elif "communication" in signal_type:
            return "unknown"
        return "unknown"

    def get_electronic_order_of_battle(self) -> dict[str, Any]:
        """Generate electronic order of battle.

        Returns
        -------
        dict
            EOOB summary.
        """
        radar_signals = [s for s in self.detected_signals if "radar" in s["type"]]
        comm_signals = [s for s in self.detected_signals if "communication" in s["type"]]

        return {
            "total_signals": len(self.detected_signals),
            "radar_systems": len(radar_signals),
            "communication_systems": len(comm_signals),
            "classified_systems": sum(1 for s in self.detected_signals if s["classification"] == "military_hostile"),
            "spectrum_pressure": len(self.detected_signals) / 100.0,
        }


class CyberOperation:
    """Cyber operation for offensive and defensive actions.

    Attributes
    ----------
    operation_id : str
        Unique identifier.
    operation_type : CyberOperationType
        Type of operation.
    target_id : str
        Target agent ID.
    status : OperationStatus
        Current status.
    """

    def __init__(
        self,
        operation_id: str,
        operation_type: CyberOperationType,
        target_id: str,
    ) -> None:
        self.operation_id = operation_id
        self.operation_type = operation_type
        self.target_id = target_id
        self.status = OperationStatus.PLANNING
        self.resources_required: float = 10.0
        self.success_probability: float = 0.5
        self.effects: list[dict] = []

    def execute(self, attacker_capability: float) -> dict[str, Any]:
        """Execute cyber operation.

        Parameters
        ----------
        attacker_capability : float
            Attacker's cyber capability [0.0, 1.0].

        Returns
        -------
        dict
            Operation result.
        """
        self.status = OperationStatus.ACTIVE

        if self.operation_type == CyberOperationType.RECON:
            return self._execute_recon(attacker_capability)
        elif self.operation_type == CyberOperationType.EXPLOIT:
            return self._execute_exploit(attacker_capability)
        elif self.operation_type == CyberOperationType.DENIAL:
            return self._execute_denial(attacker_capability)
        elif self.operation_type == CyberOperationType.DESTRUCTION:
            return self._execute_destruction(attacker_capability)

        return {"success": False, "reason": "unknown_operation_type"}

    def _execute_recon(self, capability: float) -> dict[str, Any]:
        """Execute reconnaissance operation."""
        success = random.random() < capability * 0.8

        if success:
            self.status = OperationStatus.SUCCESS
            return {
                "success": True,
                "discovery": "network_topology",
                "vulnerabilities": random.randint(2, 5),
                "data_exfiltrated": random.uniform(0.1, 0.5),
            }
        else:
            self.status = OperationStatus.FAILURE
            return {"success": False, "reason": "detected"}

    def _execute_exploit(self, capability: float) -> dict[str, Any]:
        """Execute exploitation operation."""
        success = random.random() < capability * 0.6

        if success:
            self.status = OperationStatus.SUCCESS
            return {
                "success": True,
                "exploit_type": "privilege_escalation",
                "persistence": capability > 0.5,
                "lateral_movement": random.random() < capability * 0.4,
            }
        else:
            self.status = OperationStatus.FAILURE
            return {"success": False, "reason": "patch_applied"}

    def _execute_denial(self, capability: float) -> dict[str, Any]:
        """Execute denial of service operation."""
        success = random.random() < capability * 0.7

        if success:
            duration = random.uniform(1.0, 24.0)
            self.status = OperationStatus.SUCCESS
            self.effects.append({"type": "denial", "duration": duration})
            return {
                "success": True,
                "service_affected": random.choice(["web", "email", "dns"]),
                "duration_hours": duration,
            }
        else:
            self.status = OperationStatus.DETECTED
            return {"success": False, "reason": "detected", "countermeasures": True}

    def _execute_destruction(self, capability: float) -> dict[str, Any]:
        """Execute destructive operation."""
        success = random.random() < capability * 0.3

        if success:
            self.status = OperationStatus.SUCCESS
            self.effects.append({"type": "destruction", "severity": "critical"})
            return {
                "success": True,
                "target_systems": random.randint(1, 3),
                "recovery_time_hours": random.randint(24, 168),
            }
        else:
            self.status = OperationStatus.FAILURE
            return {"success": False, "reason": "air_gap_detected"}


class CyberOperationManager:
    """Manage multiple cyber operations."""

    def __init__(self, owner_id: str) -> None:
        self.owner_id = owner_id
        self.operations: list[CyberOperation] = []
        self.capability: float = 0.5

    def plan_operation(
        self,
        operation_type: CyberOperationType,
        target_id: str,
    ) -> CyberOperation:
        """Plan a new cyber operation.

        Parameters
        ----------
        operation_type : CyberOperationType
            Type of operation.
        target_id : str
            Target agent ID.

        Returns
        -------
        CyberOperation
            Planned operation.
        """
        operation_id = f"op_{len(self.operations)}_{self.owner_id}"
        operation = CyberOperation(operation_id, operation_type, target_id)

        self.operations.append(operation)
        return operation

    def execute_operations(self) -> list[dict[str, Any]]:
        """Execute all planned operations.

        Returns
        -------
        list[dict]
            Results of all operations.
        """
        results = []

        for op in self.operations:
            if op.status == OperationStatus.PLANNING:
                result = op.execute(self.capability)
                results.append(result)

        return results

    def get_active_operations(self) -> list[CyberOperation]:
        """Get currently active operations."""
        return [op for op in self.operations if op.status == OperationStatus.ACTIVE]
