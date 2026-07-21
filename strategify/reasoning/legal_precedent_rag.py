"""Legal Precedent RAG for retrieving treaty and case law arguments.

Retrieval Augmented Generation system for legal dispute resolution,
supporting precedent-based argument retrieval for geopolitical simulations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LegalPrecedent:
    """A legal precedent for dispute resolution."""

    precedent_id: str
    case_name: str
    tribunal: str
    year: int
    domain: str
    summary: str
    key_holdings: list[str] = field(default_factory=list)
    legal_principle: str = ""
    applicability: list[str] = field(default_factory=list)
    relevance_score: float = 0.0


@dataclass
class LegalArgument:
    """A legal argument based on precedent."""

    argument_id: str
    premise: str
    legal_basis: str
    supporting_precedents: list[str] = field(default_factory=list)
    counter_arguments: list[str] = field(default_factory=list)
    strength: float = 0.5


@dataclass
class RAGQuery:
    """Query for legal precedent retrieval."""

    query_text: str
    domain: str
    dispute_type: str
    parties: list[str] = field(default_factory=list)
    time_period: tuple[int, int] | None = None


class LegalPrecedentDatabase:
    """Database of legal precedents for retrieval."""

    def __init__(self) -> None:
        self.precedents: list[LegalPrecedent] = []
        self._load_default_precedents()

    def _load_default_precedents(self) -> None:
        """Load default legal precedents."""
        self.precedents = [
            LegalPrecedent(
                precedent_id="icj_nicaragua_1986",
                case_name="Nicaragua v. United States",
                tribunal="International Court of Justice",
                year=1986,
                domain="international",
                summary="Case concerning military and paramilitary activities against Nicaragua.",
                key_holdings=[
                    "Use of force prohibited except in self-defense",
                    "Non-intervention in internal affairs is customary law",
                    "Armed attack threshold requires significant scale",
                ],
                legal_principle="Article 2(4) UN Charter - prohibition on force",
                applicability=["self-defense_claims", "armed_intervention", "proxy_warfare"],
            ),
            LegalPrecedent(
                precedent_id="icj_corfu_1949",
                case_name="Corfu Channel Case",
                tribunal="International Court of Justice",
                year=1949,
                domain="international",
                summary="Albania sued UK for naval minesweeping in territorial waters.",
                key_holdings=[
                    "Territorial waters are subject to sovereignty",
                    "Innocent passage must be respected",
                    "State responsibility for territory",
                ],
                legal_principle="UNCLOS - freedom of navigation and territorial sovereignty",
                applicability=["territorial_disputes", "naval_operations", "maritime_rights"],
            ),
            LegalPrecedent(
                precedent_id="icj_tehran_1980",
                case_name="United States v. Iran",
                tribunal="International Court of Justice",
                year=1980,
                domain="diplomatic",
                summary="US diplomatic hostages case - diplomatic immunity and state responsibility.",
                key_holdings=[
                    "Diplomatic premises are inviolable",
                    "Host state must protect diplomatic property",
                    "State responsible for actions of revolutionary elements",
                ],
                legal_principle="Vienna Convention on Diplomatic Relations 1961",
                applicability=["diplomatic_incidents", "hostage_situations", "embassy_protection"],
            ),
            LegalPrecedent(
                precedent_id="icty_tadic_1995",
                case_name="Prosecutor v. Tadic",
                tribunal="International Criminal Tribunal for former Yugoslavia",
                year=1995,
                domain="war_crimes",
                summary="FirstICTY case establishing command responsibility.",
                key_holdings=[
                    "Command responsibility for war crimes",
                    "Distinction between international and non-international conflicts",
                    "Individual criminal responsibility established",
                ],
                legal_principle="Geneva Conventions - common article 3",
                applicability=["war_crimes", "command_responsibility", "civilian_protection"],
            ),
            LegalPrecedent(
                precedent_id="icj_aerial_1956",
                case_name="Aerospace Law - Aerial Incident",
                tribunal="International Court of Justice",
                year=1956,
                domain="air_space",
                summary="Case concerning aerial incidents and air space sovereignty.",
                key_holdings=[
                    "Air space is integral part of territorial sovereignty",
                    "Shooting down aircraft requires clear evidence of hostile intent",
                    "Innocent passage applies to aircraft",
                ],
                legal_principle="Chicago Convention - air space sovereignty",
                applicability=["aerial_incidents", "air_space_violations", "shootdown_cases"],
            ),
            LegalPrecedent(
                precedent_id="icj_border_1992",
                case_name="Land, Island and Frontier Dispute",
                tribunal="International Court of Justice",
                year=1992,
                domain="territorial",
                summary="Territorial boundary dispute case.",
                key_holdings=[
                    "Uti possidetis juris - existing boundaries preserved",
                    "Effectivites can override treaty text",
                    "Critical date doctrine for territorial claims",
                ],
                legal_principle="Treaty interpretation and state practice",
                applicability=["border_disputes", "territorial_claims", "frontier_disputes"],
            ),
            LegalPrecedent(
                precedent_id="icj_sea_1982",
                case_name="Maritime Delimitation Case",
                tribunal="International Court of Justice",
                year=1982,
                domain="maritime",
                summary="Case concerning maritime boundaries and exclusive economic zones.",
                key_holdings=[
                    "Equidistance method for maritime boundaries",
                    "Economic factors in delimitation",
                    "Geography overrides equity",
                ],
                legal_principle="UNCLOS - exclusive economic zones",
                applicability=["maritime_disputes", "eez_claims", "fishing_rights"],
            ),
            LegalPrecedent(
                precedent_id="icj_gabcikovo_1997",
                case_name="Gabcikovo-Nagymaros Project",
                tribunal="International Court of Justice",
                year=1997,
                domain="environment",
                summary="Hungary v. Slovakia - treaty termination and environmental obligations.",
                key_holdings=[
                    "Fundamental change of circumstances requires strict test",
                    "Environmental norms are part of treaty interpretation",
                    "Treaty cannot be terminated unilaterally",
                ],
                legal_principle="Vienna Convention Article 62 - fundamental change",
                applicability=["treaty_termination", "environmental_damages", "unilateral_withdrawal"],
            ),
        ]

    def add_precedent(self, precedent: LegalPrecedent) -> None:
        """Add a precedent to the database."""
        self.precedents.append(precedent)

    def get_precedents_by_domain(self, domain: str) -> list[LegalPrecedent]:
        """Get all precedents in a domain."""
        return [p for p in self.precedents if p.domain == domain]

    def get_precedents_by_year_range(self, start_year: int, end_year: int) -> list[LegalPrecedent]:
        """Get precedents within a year range."""
        return [p for p in self.precedents if start_year <= p.year <= end_year]


class LegalPrecedentRAG:
    """RAG system for retrieving legal precedents and generating arguments."""

    def __init__(self, database: LegalPrecedentDatabase | None = None) -> None:
        self.database = database or LegalPrecedentDatabase()

    def retrieve(
        self,
        query: RAGQuery,
        top_k: int = 5,
    ) -> list[LegalPrecedent]:
        """Retrieve relevant precedents for a query."""
        candidates = []

        for precedent in self.database.precedents:
            score = self._calculate_relevance(precedent, query)
            if score > 0.0:
                precedent.relevance_score = score
                candidates.append(precedent)

        candidates.sort(key=lambda p: p.relevance_score, reverse=True)
        return candidates[:top_k]

    def _calculate_relevance(self, precedent: LegalPrecedent, query: RAGQuery) -> float:
        """Calculate relevance score for a precedent."""
        score = 0.0

        if query.domain and precedent.domain == query.domain:
            score += 0.3

        for keyword in query.query_text.lower().split():
            if keyword in precedent.case_name.lower():
                score += 0.15
            if keyword in precedent.summary.lower():
                score += 0.1
            if keyword in " ".join(precedent.key_holdings).lower():
                score += 0.1

        for applicability in precedent.applicability:
            if any(kw in applicability for kw in query.query_text.lower().split()):
                score += 0.2

        if query.time_period:
            start, end = query.time_period
            if start <= precedent.year <= end:
                score += 0.1

        return min(score, 1.0)

    def generate_argument(
        self,
        premise: str,
        legal_basis: str,
        retrieved_precedents: list[LegalPrecedent],
    ) -> LegalArgument:
        """Generate a legal argument from retrieved precedents."""
        supporting = [p.case_name for p in retrieved_precedents[:3]]

        strength = sum(p.relevance_score for p in retrieved_precedents[:3]) / 3

        return LegalArgument(
            argument_id=f"ARG_{hash(premise) % 10000:04d}",
            premise=premise,
            legal_basis=legal_basis,
            supporting_precedents=supporting,
            strength=min(strength, 1.0),
        )

    def build_legal_brief(
        self,
        query: RAGQuery,
    ) -> dict[str, Any]:
        """Build a complete legal brief from retrieval."""
        precedents = self.retrieve(query)

        arguments = []
        for i, p in enumerate(precedents[:3]):
            arg = self.generate_argument(
                premise=f"Relevant precedent: {p.case_name}",
                legal_basis=p.legal_principle,
                retrieved_precedents=[p],
            )
            arguments.append(arg)

        return {
            "query": query.query_text,
            "precedents_retrieved": len(precedents),
            "precedents": [
                {
                    "case": p.case_name,
                    "year": p.year,
                    "tribunal": p.tribunal,
                    "holdings": p.key_holdings[:2],
                    "relevance": p.relevance_score,
                }
                for p in precedents
            ],
            "arguments": [
                {
                    "premise": a.premise,
                    "basis": a.legal_basis,
                    "strength": a.strength,
                }
                for a in arguments
            ],
            "summary": self._generate_summary(precedents),
        }

    def _generate_summary(self, precedents: list[LegalPrecedent]) -> str:
        """Generate summary of retrieved precedents."""
        if not precedents:
            return "No relevant precedents found"

        cases = ", ".join([f"{p.case_name} ({p.year})" for p in precedents[:3]])
        return f"Based on {len(precedents)} relevant precedents including {cases}"

    def retrieve_precedents_for_dispute(
        self,
        dispute_topic: str,
        domain: str,
        parties: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Quick retrieval for dispute scenarios."""
        query = RAGQuery(
            query_text=dispute_topic,
            domain=domain,
            dispute_type="general",
            parties=parties or [],
        )
        brief = self.build_legal_brief(query)
        return brief.get("precedents", [])


def create_legal_rag() -> LegalPrecedentRAG:
    """Factory function to create legal RAG system."""
    return LegalPrecedentRAG()


def quick_precedent_search(
    query: str,
    domain: str = "international",
) -> list[dict[str, Any]]:
    """Quick search for legal precedents."""
    rag = create_legal_rag()
    q = RAGQuery(query_text=query, domain=domain, dispute_type="general")
    brief = rag.build_legal_brief(q)
    return brief.get("precedents", [])
