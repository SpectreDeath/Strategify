"""Military occupation mapping and personnel management.

This module maps real-world military occupations to simulation capabilities:
- MilitaryOccupation: SOC code mapping with skills and training
- PersonnelManagement: Skill-based assignment and training pipeline

SOC Codes:
- 55-3010: Unmanned Aircraft Systems Operators
- 55-2030: Intelligence Analysts
- 55-4010: Cyber Operations Specialists
- 55-3011: Military Intelligence Analysts
- 55-3012: Crime and Intelligence Analysts
- 55-3013: Military Logistics Analysts
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class OccupationCategory(Enum):
    """Military occupation categories."""

    INTELLIGENCE = "intelligence"
    CYBER = "cyber"
    OPERATIONS = "operations"
    LOGISTICS = "logistics"
    COMBAT = "combat"
    MEDICAL = "medical"
    ENGINEERING = "engineering"


@dataclass
class SkillRequirement:
    """Required skill for an occupation."""

    skill_name: str
    proficiency_level: float
    training_hours: int


@dataclass
class MilitaryOccupation:
    """A military occupation with SOC code mapping.

    Attributes
    ----------
    occupation_id : str
        Unique identifier.
    name : str
        Occupation name.
    soc_code : str
        Standard Occupational Classification code.
    category : OccupationCategory
        Category of occupation.
    skills : list[SkillRequirement]
        Required skills.
    training_duration_months : int
        Training time required.
    clearance_level : int
        Required security clearance (1-5).
    active_duty_only : bool
        Whether only active duty can hold this.
    """

    occupation_id: str
    name: str
    soc_code: str
    category: OccupationCategory
    skills: list[SkillRequirement]
    training_duration_months: int
    clearance_level: int = 2
    active_duty_only: bool = False

    def get_skill_names(self) -> list[str]:
        """Get list of skill names."""
        return [s.skill_name for s in self.skills]

    def meets_requirements(self, personnel: PersonnelRecord) -> bool:
        """Check if personnel meets occupation requirements."""
        if personnel.clearance_level < self.clearance_level:
            return False

        if self.active_duty_only and not personnel.is_active_duty:
            return False

        for skill in self.skills:
            personnel_skill = personnel.skills.get(skill.skill_name, 0.0)
            if personnel_skill < skill.proficiency_level * 0.8:
                return False

        return True


@dataclass
class PersonnelRecord:
    """A personnel record for an individual.

    Attributes
    ----------
    personnel_id : str
        Unique identifier.
    name : str
        Full name.
    rank : str
        Military rank.
    branch : str
        Service branch.
    occupation : MilitaryOccupation | None
        Assigned occupation.
    skills : dict[str, float]
        Skill proficiency levels [0.0, 1.0].
    experience_years : float
        Years of experience.
    clearance_level : int
        Security clearance level.
    is_active_duty : bool
        Whether active duty.
    training_history : list[dict]
        Training completion history.
    """

    personnel_id: str
    name: str
    rank: str
    branch: str
    occupation: MilitaryOccupation | None = None
    skills: dict[str, float] = field(default_factory=dict)
    experience_years: float = 0.0
    clearance_level: int = 1
    is_active_duty: bool = True
    training_history: list[dict] = field(default_factory=list)

    def add_skill(self, skill_name: str, proficiency: float) -> None:
        """Add or update a skill."""
        self.skills[skill_name] = min(1.0, max(0.0, proficiency))

    def gain_experience(self, years: float) -> None:
        """Gain experience and improve skills."""
        self.experience_years += years

        for skill_name in self.skills:
            growth = years * 0.05
            self.skills[skill_name] = min(1.0, self.skills[skill_name] + growth)


class PersonnelManagement:
    """Manage military personnel assignment and training.

    Attributes
    ----------
    unit_id : str
        Unit that owns this management system.
    """

    def __init__(self, unit_id: str) -> None:
        self.unit_id = unit_id
        self.personnel: list[PersonnelRecord] = []
        self.occupation_standards: dict[str, MilitaryOccupation] = {}
        self._initialize_occupation_standards()

    def _initialize_occupation_standards(self) -> None:
        """Initialize standard military occupations."""
        self.occupation_standards["55-3010"] = MilitaryOccupation(
            occupation_id="55-3010",
            name="Unmanned Aircraft Systems Operator",
            soc_code="55-3010",
            category=OccupationCategory.OPERATIONS,
            skills=[
                SkillRequirement("remote_piloting", 0.7, 120),
                SkillRequirement("sensor_operations", 0.6, 80),
                SkillRequirement("data_analysis", 0.5, 60),
            ],
            training_duration_months=6,
            clearance_level=3,
            active_duty_only=True,
        )

        self.occupation_standards["55-2030"] = MilitaryOccupation(
            occupation_id="55-2030",
            name="Intelligence Analyst",
            soc_code="55-2030",
            category=OccupationCategory.INTELLIGENCE,
            skills=[
                SkillRequirement("analysis", 0.8, 160),
                SkillRequirement("research", 0.7, 120),
                SkillRequirement("reporting", 0.6, 80),
                SkillRequirement("language", 0.5, 200),
            ],
            training_duration_months=9,
            clearance_level=4,
            active_duty_only=False,
        )

        self.occupation_standards["55-4010"] = MilitaryOccupation(
            occupation_id="55-4010",
            name="Cyber Operations Specialist",
            soc_code="55-4010",
            category=OccupationCategory.CYBER,
            skills=[
                SkillRequirement("network_security", 0.8, 160),
                SkillRequirement("penetration_testing", 0.7, 120),
                SkillRequirement("coding", 0.6, 100),
                SkillRequirement("forensics", 0.5, 80),
            ],
            training_duration_months=12,
            clearance_level=5,
            active_duty_only=True,
        )

        self.occupation_standards["55-3011"] = MilitaryOccupation(
            occupation_id="55-3011",
            name="Military Intelligence Analyst",
            soc_code="55-3011",
            category=OccupationCategory.INTELLIGENCE,
            skills=[
                SkillRequirement("tactical_analysis", 0.7, 100),
                SkillRequirement("threat_assessment", 0.8, 120),
                SkillRequirement("geospatial", 0.6, 80),
                SkillRequirement("briefing", 0.5, 40),
            ],
            training_duration_months=8,
            clearance_level=3,
            active_duty_only=False,
        )

        self.occupation_standards["55-3013"] = MilitaryOccupation(
            occupation_id="55-3013",
            name="Military Logistics Analyst",
            soc_code="55-3013",
            category=OccupationCategory.LOGISTICS,
            skills=[
                SkillRequirement("supply_chain", 0.7, 80),
                SkillRequirement("resource_planning", 0.6, 60),
                SkillRequirement("data_analysis", 0.6, 60),
            ],
            training_duration_months=4,
            clearance_level=2,
            active_duty_only=False,
        )

    def add_personnel(self, personnel: PersonnelRecord) -> bool:
        """Add personnel to the unit.

        Parameters
        ----------
        personnel : PersonnelRecord
            Personnel to add.

        Returns
        -------
        bool
            True if added successfully.
        """
        if any(p.personnel_id == personnel.personnel_id for p in self.personnel):
            logger.warning(
                "Personnel %s already exists in unit %s",
                personnel.personnel_id,
                self.unit_id,
            )
            return False

        self.personnel.append(personnel)
        logger.debug(
            "Added personnel %s to unit %s",
            personnel.personnel_id,
            self.unit_id,
        )
        return True

    def assign_occupation(
        self,
        personnel_id: str,
        occupation_id: str,
    ) -> bool:
        """Assign occupation to personnel.

        Parameters
        ----------
        personnel_id : str
            Personnel to assign.
        occupation_id : str
            Occupation SOC code.

        Returns
        -------
        bool
            True if assignment successful.
        """
        occupation = self.occupation_standards.get(occupation_id)
        if not occupation:
            logger.error("Unknown occupation: %s", occupation_id)
            return False

        personnel = self._find_personnel(personnel_id)
        if not personnel:
            logger.error("Personnel not found: %s", personnel_id)
            return False

        if not occupation.meets_requirements(personnel):
            logger.warning(
                "Personnel %s does not meet requirements for %s",
                personnel_id,
                occupation_id,
            )
            return False

        personnel.occupation = occupation

        for skill in occupation.skills:
            if skill.skill_name not in personnel.skills:
                personnel.skills[skill.skill_name] = 0.0

        return True

    def _find_personnel(self, personnel_id: str) -> PersonnelRecord | None:
        """Find personnel by ID."""
        for p in self.personnel:
            if p.personnel_id == personnel_id:
                return p
        return None

    def get_available_for_assignment(
        self,
        occupation_id: str,
    ) -> list[PersonnelRecord]:
        """Get personnel available for occupation assignment.

        Parameters
        ----------
        occupation_id : str
            Occupation SOC code.

        Returns
        -------
        list[PersonnelRecord]
            Available personnel.
        """
        occupation = self.occupation_standards.get(occupation_id)
        if not occupation:
            return []

        available = []
        for p in self.personnel:
            if p.occupation is None and occupation.meets_requirements(p):
                available.append(p)

        return available

    def assign_to_positions(
        self,
        required_occupations: dict[str, int],
    ) -> dict[str, list[str]]:
        """Assign personnel to fill required positions.

        Parameters
        ----------
        required_occupations : dict[str, int]
            Map of occupation SOC code to required count.

        Returns
        -------
        dict
            Assignment results with assigned personnel IDs.
        """
        assignments: dict[str, list[str]] = {}

        for occupation_id, count in required_occupations.items():
            available = self.get_available_for_assignment(occupation_id)

            assigned_ids = []
            for personnel in available[:count]:
                if self.assign_occupation(personnel.personnel_id, occupation_id):
                    assigned_ids.append(personnel.personnel_id)

            assignments[occupation_id] = assigned_ids

        return assignments

    def train_personnel(
        self,
        personnel_id: str,
        skill_name: str,
        hours: int,
    ) -> bool:
        """Train personnel on a skill.

        Parameters
        ----------
        personnel_id : str
            Personnel to train.
        skill_name : str
            Skill to train.
        hours : int
            Training hours.

        Returns
        -------
        bool
            True if training successful.
        """
        personnel = self._find_personnel(personnel_id)
        if not personnel:
            return False

        proficiency_gain = hours / 100.0 * (1.0 - personnel.skills.get(skill_name, 0.0))

        current = personnel.skills.get(skill_name, 0.0)
        personnel.skills[skill_name] = min(1.0, current + proficiency_gain)

        personnel.training_history.append(
            {
                "skill": skill_name,
                "hours": hours,
                "proficiency": personnel.skills[skill_name],
            }
        )

        return True

    def get_unit_capability(self) -> dict[str, float]:
        """Calculate overall unit capability scores.

        Returns
        -------
        dict
            Capability scores by category.
        """
        capabilities: dict[OccupationCategory, list[float]] = {cat: [] for cat in OccupationCategory}

        for p in self.personnel:
            if p.occupation:
                category = p.occupation.category
                skill_avg = np.mean(list(p.skills.values())) if p.skills else 0.0
                experience_factor = min(1.0, p.experience_years / 10.0)
                capabilities[category].append(skill_avg * 0.7 + experience_factor * 0.3)

        result = {}
        for category, scores in capabilities.items():
            result[category.value] = np.mean(scores) if scores else 0.0

        return result

    def get_manpower_summary(self) -> dict[str, Any]:
        """Get manpower summary statistics.

        Returns
        -------
        dict
            Manpower summary.
        """
        total = len(self.personnel)
        if total == 0:
            return {"total": 0, "by_branch": {}, "by_occupation": {}}

        by_branch: dict[str, int] = {}
        by_occupation: dict[str, int] = {}

        for p in self.personnel:
            by_branch[p.branch] = by_branch.get(p.branch, 0) + 1

            if p.occupation:
                by_occupation[p.occupation.name] = by_occupation.get(p.occupation.name, 0) + 1
            else:
                by_occupation["Unassigned"] = by_occupation.get("Unassigned", 0) + 1

        return {
            "total": total,
            "by_branch": by_branch,
            "by_occupation": by_occupation,
            "clearance_distribution": self._get_clearance_distribution(),
        }

    def _get_clearance_distribution(self) -> dict[int, int]:
        """Get distribution of clearance levels."""
        distribution: dict[int, int] = {}
        for p in self.personnel:
            distribution[p.clearance_level] = distribution.get(p.clearance_level, 0) + 1
        return distribution
