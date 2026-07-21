"""Military operations research and optimization modules.

This package provides:
- ForceAllocationOptimizer: Optimize unit distribution across theaters
- ConflictPredictor: Predict conflict likelihood based on force posture
- WarGamingEngine: Monte Carlo conflict simulations
- AutonomousSystem: Drone management with autonomy levels
- ISRPlatform: ISR platform management
- UAVSwarm: Coordinated drone operations
- ElectronicWarfareSystem: Jamming, ECM, electronic attack/defense
- EMSpectrumManager: Frequency allocation, signal classification
- CyberOperation: Offensive and defensive cyber operations
- MilitaryOccupation: SOC code mapping with skills and training
- PersonnelManagement: Skill-based assignment and training pipeline
"""

from __future__ import annotations

from strategify.military.autonomous_systems import (
    AutonomousSystem,
    ISRPlatform,
    UAVSwarm,
)
from strategify.military.electronic_warfare import (
    CyberOperation,
    CyberOperationManager,
    ElectronicWarfareSystem,
    EMSpectrumManager,
)
from strategify.military.occupations import (
    MilitaryOccupation,
    PersonnelManagement,
    PersonnelRecord,
)
from strategify.military.operations_research import (
    ConflictPredictor,
    ForceAllocationOptimizer,
    WarGamingEngine,
)

__all__ = [
    "ForceAllocationOptimizer",
    "ConflictPredictor",
    "WarGamingEngine",
    "AutonomousSystem",
    "ISRPlatform",
    "UAVSwarm",
    "ElectronicWarfareSystem",
    "EMSpectrumManager",
    "CyberOperation",
    "CyberOperationManager",
    "MilitaryOccupation",
    "PersonnelManagement",
    "PersonnelRecord",
]
