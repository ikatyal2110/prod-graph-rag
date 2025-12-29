"""Service for asking questions and generating deterministic answers"""

from typing import List

from app.db import Neo4jClient
from app.services.retrieval import RetrievalService
from app.services.explain import ExplainService
from app.models.api import AskResponse, ExplainResponse, Fact, Evidence
from app.logging import get_logger

logger = get_logger(__name__)


class AskService:
    """Service for asking questions and generating deterministic answers"""
    
    def __init__(
        self,
        neo4j_client: Neo4jClient,
        retrieval_service: RetrievalService,
        explain_service: ExplainService
    ):
        """
        Initialize ask service.
        
        Args:
            neo4j_client: Neo4j client instance
            retrieval_service: Retrieval service instance
            explain_service: Explain service instance
        """
        self.neo4j_client = neo4j_client
        self.retrieval_service = retrieval_service
        self.explain_service = explain_service
    
    def ask(
        self,
        question: str,
        max_incidents: int = 1,
        max_facts: int = 12
    ) -> AskResponse:
        """
        Ask a question and generate a deterministic answer.
        
        Args:
            question: User question
            max_incidents: Maximum incidents to include
            max_facts: Maximum key facts to return
            
        Returns:
            AskResponse with answer, evidence, key facts, and incident cards
        """
        logger.info(f"Asking question: {question}, max_incidents={max_incidents}, max_facts={max_facts}")
        
        # Step 1: Use retrieval service to get anchors, incidents, and facts
        anchors, facts, evidence, stats, _ = self.retrieval_service.retrieve(
            question=question,
            max_hops=2,
            max_paths=300,
            max_facts=200,  # Get more facts initially for filtering
            max_anchors=6,
            max_incidents=max_incidents,
            debug=False
        )
        
        incident_ids = evidence.incident_ids
        logger.info(f"Retrieved {len(incident_ids)} incidents: {incident_ids}")
        
        # Step 2: Get incident cards for each selected incident
        incident_cards = []
        for incident_id in incident_ids:
            try:
                explain_response = self.explain_service.explain_incident(
                    incident_id=incident_id,
                    include_facts=False  # Don't include facts in cards
                )
                incident_cards.append(explain_response)
            except ValueError as e:
                logger.warning(f"Could not explain incident {incident_id}: {e}")
                # Continue with other incidents
        
        # Step 3: Select and sort key facts deterministically
        # First, prioritize and sort by relationship type
        key_facts = self._sort_key_facts(facts)[:max_facts]
        
        logger.info(f"Selected {len(key_facts)} key facts from {len(facts)} total facts")
        
        # Step 4: Build deterministic answer
        answer = self._build_answer(incident_cards)
        
        logger.info(f"Generated answer for question: {question[:50]}...")
        
        return AskResponse(
            question=question,
            answer=answer,
            evidence=evidence,
            key_facts=key_facts,
            incident_cards=incident_cards
        )
    
    def _build_answer(self, incident_cards: List[ExplainResponse]) -> str:
        """
        Build deterministic answer from incident cards.
        
        Args:
            incident_cards: List of explain responses for incidents
            
        Returns:
            Deterministic narrative answer
        """
        if not incident_cards:
            return "No matching incidents found for this question."
        
        if len(incident_cards) == 1:
            # Single incident: use dedicated formatter
            return self._format_single_incident_answer(incident_cards[0])
        else:
            # Multiple incidents: produce ranked list
            return self._format_multiple_incidents_answer(incident_cards)
    
    def _format_single_incident_answer(self, inc: ExplainResponse) -> str:
        """
        Format answer for a single incident using deterministic template.
        
        Template:
        - First sentence: "Most relevant incident: <INCIDENT_ID>."
        - Second sentence: "Component: <COMPONENT>. Failure mode: <FAILURE_MODE>."
        - Third sentence (if present): "Root cause: <ROOT_CAUSE>."
        - Fourth sentence (if present): "Trigger: <TRIGGER>."
        - Artifacts line (if present): "Artifacts: <ARTIFACT_1>, <ARTIFACT_2>, ... ."
        - Final sentence: "Evidence is grounded in graph relationships and linked nodes."
        
        Args:
            inc: Explain response for the incident
            
        Returns:
            Formatted answer string
        """
        sentences = []
        
        # First sentence: Incident ID (title not available in current schema)
        sentences.append(f"Most relevant incident: {inc.incident_id}.")
        
        # Second sentence: Component + Failure mode
        if not inc.affects or not inc.failure_modes:
            # If either is missing, format what we have separately
            if inc.affects:
                components = sorted(inc.affects)
                comp_str = ", ".join(components)
                sentences.append(f"Component: {comp_str}.")
            if inc.failure_modes:
                failure_modes = sorted(inc.failure_modes)
                fm_str = ", ".join(failure_modes)
                sentences.append(f"Failure mode: {fm_str}.")
        else:
            components = sorted(inc.affects)
            failure_modes = sorted(inc.failure_modes)
            comp_str = ", ".join(components)
            fm_str = ", ".join(failure_modes)
            sentences.append(f"Component: {comp_str}. Failure mode: {fm_str}.")
        
        # Third sentence: Root cause (only if present)
        if inc.root_causes:
            root_causes = sorted(inc.root_causes)
            root_cause_str = ", ".join(root_causes)
            sentences.append(f"Root cause: {root_cause_str}.")
        
        # Fourth sentence: Trigger (only if present)
        if inc.triggers:
            triggers = sorted(inc.triggers)
            trigger_str = ", ".join(triggers)
            sentences.append(f"Trigger: {trigger_str}.")
        
        # Artifacts line (only if present)
        if inc.artifacts:
            artifacts = sorted(inc.artifacts)  # Sort for determinism
            artifact_str = ", ".join(artifacts)
            sentences.append(f"Artifacts: {artifact_str}.")
        
        # Final sentence: always present
        sentences.append("Evidence is grounded in graph relationships and linked nodes.")
        
        # Join sentences with spaces and ensure proper formatting
        answer = " ".join(sentences)
        # Clean up any double spaces
        while "  " in answer:
            answer = answer.replace("  ", " ")
        
        return answer.strip()
    
    def _format_multiple_incidents_answer(self, incident_cards: List[ExplainResponse]) -> str:
        """
        Format answer for multiple incidents.
        
        Args:
            incident_cards: List of explain responses for incidents
            
        Returns:
            Formatted answer string
        """
        answer_parts = [f"Found {len(incident_cards)} relevant incidents:"]
        
        for idx, inc in enumerate(incident_cards[:5], 1):  # Limit to top 5
            inc_parts = [f"{idx}. Incident {inc.incident_id}"]
            
            if inc.affects:
                comp_str = ", ".join(sorted(inc.affects[:2]))
                inc_parts.append(f"affects {comp_str}")
            if inc.failure_modes:
                inc_parts.append(f"exhibits {sorted(inc.failure_modes)[0]}")
            if inc.root_causes:
                inc_parts.append(f"caused by {sorted(inc.root_causes)[0]}")
            
            answer_parts.append(" ".join(inc_parts))
        
        answer = ". ".join(answer_parts) + "."
        return answer
    
    def _sort_key_facts(self, facts: List[Fact]) -> List[Fact]:
        """
        Sort facts deterministically by relationship type and target.
        
        Primary sort order (by rel):
        1. AFFECTS
        2. EXHIBITS
        3. CAUSED_BY
        4. TRIGGERED_BY
        5. INVOLVES
        6. USES
        
        Secondary sort (within same rel):
        - Sort by "to" lexicographically
        - Then by "from" if "to" is equal
        
        Unknown rel types are placed after known ones, sorted lexicographically by rel name,
        then by "to", then by "from".
        
        Args:
            facts: List of Fact objects to sort
            
        Returns:
            Sorted list of Fact objects (new list, input not mutated)
        """
        # Define relationship type priority order (only the 6 required types)
        rel_priority = {
            'AFFECTS': 1,
            'EXHIBITS': 2,
            'CAUSED_BY': 3,
            'TRIGGERED_BY': 4,
            'INVOLVES': 5,
            'USES': 6
        }
        
        # Create a copy to avoid mutating input
        facts_copy = list(facts)
        
        def fact_sort_key(fact: Fact) -> tuple:
            """
            Generate sort key for a fact.
            Returns: (rel_rank, rel_name, to_id, from_id)
            - rel_rank: priority number (1-6 for known rels, 999 for unknown)
            - rel_name: lexicographic sort for unknown rels or tie-breaking
            - to_id: secondary sort within same rel
            - from_id: tertiary sort if to_id is equal
            """
            rel_name = fact.rel
            rel_rank = rel_priority.get(rel_name, 999)  # Unknown rels get high rank
            
            return (rel_rank, rel_name, fact.to_id, fact.from_id)
        
        # Sort facts
        sorted_facts = sorted(facts_copy, key=fact_sort_key)
        
        # De-duplicate exact duplicates (same from, rel, to)
        deduplicated = []
        seen = set()
        for fact in sorted_facts:
            fact_tuple = (fact.from_id, fact.rel, fact.to_id)
            if fact_tuple not in seen:
                seen.add(fact_tuple)
                deduplicated.append(fact)
        
        return deduplicated
