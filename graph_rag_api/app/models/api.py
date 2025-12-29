"""Pydantic models for API requests and responses"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Anchor(BaseModel):
    """Anchor entity found from question"""
    id: str = Field(..., description="Entity ID")
    type: str = Field(..., description="Entity type")


class Fact(BaseModel):
    """Graph fact (relationship)"""
    from_id: str = Field(..., alias="from", description="Source entity ID")
    rel: str = Field(..., description="Relationship type")
    to_id: str = Field(..., alias="to", description="Target entity ID")
    
    class Config:
        populate_by_name = True


class Evidence(BaseModel):
    """Evidence collected from graph"""
    incident_ids: List[str] = Field(..., description="List of incident IDs found in subgraph")


class Stats(BaseModel):
    """Query statistics"""
    node_count: int = Field(..., description="Number of nodes in subgraph")
    rel_count: int = Field(..., description="Number of relationships in subgraph")


class QueryRequest(BaseModel):
    """Query request model"""
    question: str = Field(..., min_length=1, description="User question")
    max_hops: int = Field(default=2, ge=1, le=3, description="Maximum graph traversal depth")
    max_paths: int = Field(default=300, ge=1, le=1000, description="Maximum paths to return")
    max_facts: int = Field(default=120, ge=1, le=500, description="Maximum facts to return")
    max_incidents: int = Field(default=1, ge=1, le=10, description="Maximum incidents to include in evidence")
    debug: bool = Field(default=False, description="Include debug information in response")


class DebugInfo(BaseModel):
    """Debug information for queries"""
    tokens_used: List[str] = Field(default=[], description="Tokens extracted from question")
    anchor_candidates: Optional[List[dict]] = Field(default=None, description="Top anchor candidates with scores")
    anchors: Optional[List[dict]] = Field(default=None, description="Selected anchors with types")
    candidate_incidents: Optional[List[dict]] = Field(default=None, description="All candidate incidents with scores and matched anchors")
    chosen_incidents: List[str] = Field(default=[], description="Incidents selected after ranking")


class QueryResponse(BaseModel):
    """Query response model"""
    question: str = Field(..., description="Original question")
    anchors: List[Anchor] = Field(..., description="Anchor entities found")
    facts: List[Fact] = Field(..., description="Extracted facts (relationships)")
    evidence: Evidence = Field(..., description="Evidence collected")
    stats: Stats = Field(..., description="Query statistics")
    debug: Optional[DebugInfo] = Field(default=None, description="Debug information (if requested)")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(default="ok", description="Service status")


class ExplainRequest(BaseModel):
    """Explain incident request model"""
    incident_id: str = Field(..., min_length=1, description="Incident ID to explain")
    include_facts: bool = Field(default=True, description="Whether to include facts in response")


class FactDetail(BaseModel):
    """Fact detail for explain response"""
    from_id: str = Field(..., alias="from", description="Source entity ID")
    rel: str = Field(..., description="Relationship type")
    to_id: str = Field(..., alias="to", description="Target entity ID")
    
    class Config:
        populate_by_name = True


class ExplainResponse(BaseModel):
    """Explain incident response model"""
    incident_id: str = Field(..., description="Incident ID")
    severity: Optional[str] = Field(default=None, description="Incident severity (high/medium/low)")
    affects: List[str] = Field(default=[], description="Components affected by this incident")
    failure_modes: List[str] = Field(default=[], description="Failure modes exhibited by this incident")
    root_causes: List[str] = Field(default=[], description="Root causes of this incident")
    triggers: List[str] = Field(default=[], description="Triggers that activated this incident")
    concepts: List[str] = Field(default=[], description="Concepts involved in this incident")
    artifacts_direct: List[str] = Field(default=[], description="Artifacts directly connected to this incident")
    artifacts_derived: List[str] = Field(default=[], description="Artifacts used by components affected by this incident")
    artifacts: List[str] = Field(default=[], description="Union of direct and derived artifacts")
    facts: List[FactDetail] = Field(default=[], description="Facts (relationships) for this incident")


class AskRequest(BaseModel):
    """Ask question request model"""
    question: str = Field(..., min_length=1, description="User question")
    max_incidents: int = Field(default=1, ge=1, le=10, description="Maximum incidents to include")
    max_facts: int = Field(default=12, ge=1, le=50, description="Maximum key facts to return")


class AskResponse(BaseModel):
    """Ask question response model"""
    question: str = Field(..., description="Original question")
    answer: str = Field(..., description="Deterministic narrative answer")
    evidence: Evidence = Field(..., description="Evidence collected from graph")
    key_facts: List[Fact] = Field(default=[], description="Key facts (prioritized relationships)")
    incident_cards: List[ExplainResponse] = Field(default=[], description="Incident cards (explain responses without facts)")

