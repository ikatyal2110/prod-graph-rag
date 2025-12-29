"""Service for explaining incidents"""

from typing import Dict, List, Optional, Any
from collections import defaultdict

from app.db import Neo4jClient
from app.config import settings
from app.models.api import ExplainResponse, FactDetail
from app.logging import get_logger

logger = get_logger(__name__)


class ExplainService:
    """Service for explaining incidents"""
    
    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize explain service.
        
        Args:
            neo4j_client: Neo4j client instance
        """
        self.neo4j_client = neo4j_client
    
    def explain_incident(
        self,
        incident_id: str,
        include_facts: bool = True
    ) -> ExplainResponse:
        """
        Explain an incident by retrieving its relationships and categorizing them.
        
        Args:
            incident_id: ID of the incident to explain
            include_facts: Whether to include facts in the response
            
        Returns:
            ExplainResponse with categorized relationships
            
        Raises:
            ValueError: If incident is not found
        """
        logger.info(f"Explaining incident: {incident_id}, include_facts={include_facts}")
        
        try:
            with self.neo4j_client.get_session() as session:
                # Query incident and its outgoing relationships
                query = """
                MATCH (i:Entity {type:"incident", id:$incident_id})
                OPTIONAL MATCH (i)-[r:RELATIONSHIP]->(t:Entity)
                RETURN properties(i) AS incident_props,
                       collect({
                           rel: r.type, 
                           to_id: t.id, 
                           to_type: t.type,
                           to_props: properties(t)
                       }) AS outs
                """
                
                result = session.run(query, incident_id=incident_id)
                record = result.single()
                
                if not record or not record.get("incident_props"):
                    logger.warning(f"Incident not found: {incident_id}")
                    raise ValueError(f"Incident {incident_id} not found")
                
                # Extract incident properties
                incident_props = record["incident_props"]
                severity = incident_props.get("severity")
                if severity:
                    severity = severity.lower()
                    # Normalize severity values
                    if severity in ["high", "medium", "low"]:
                        severity = severity
                    else:
                        severity = None
                
                # Parse outgoing relationships
                outs = record.get("outs", [])
                
                # Initialize buckets
                affects = []
                failure_modes = []
                root_causes = []
                triggers = []
                concepts = []
                artifacts_direct = []
                facts = []
                
                # Track seen IDs for deduplication
                seen_affects = set()
                seen_failure_modes = set()
                seen_root_causes = set()
                seen_triggers = set()
                seen_concepts = set()
                seen_artifacts_direct = set()
                
                for out in outs:
                    if not out.get("to_id"):  # Skip null relationships
                        continue
                    
                    rel_type = out.get("rel")
                    to_id = out.get("to_id")
                    to_type = out.get("to_type")
                    
                    # Build fact
                    if include_facts:
                        facts.append(FactDetail(
                            from_id=incident_id,
                            rel=rel_type,
                            to_id=to_id
                        ))
                    
                    # Categorize based on relationship type and target type
                    if rel_type == "AFFECTS" and to_type == "component":
                        if to_id not in seen_affects:
                            affects.append(to_id)
                            seen_affects.add(to_id)
                    
                    elif rel_type == "EXHIBITS" and to_type == "failure_mode":
                        if to_id not in seen_failure_modes:
                            failure_modes.append(to_id)
                            seen_failure_modes.add(to_id)
                    
                    elif rel_type == "CAUSED_BY" and to_type == "root_cause":
                        if to_id not in seen_root_causes:
                            root_causes.append(to_id)
                            seen_root_causes.add(to_id)
                    
                    elif rel_type == "TRIGGERED_BY" and to_type == "trigger":
                        if to_id not in seen_triggers:
                            triggers.append(to_id)
                            seen_triggers.add(to_id)
                    
                    elif rel_type == "INVOLVES" and to_type == "concept":
                        if to_id not in seen_concepts:
                            concepts.append(to_id)
                            seen_concepts.add(to_id)
                    
                    elif rel_type == "USES" or to_type == "artifact":
                        # Direct artifacts: incident has direct edge to artifact or USES relationship
                        if to_id not in seen_artifacts_direct:
                            artifacts_direct.append(to_id)
                            seen_artifacts_direct.add(to_id)
                
                # Query derived artifacts: artifacts used by components affected by this incident
                derived_artifacts_query = """
                MATCH (i:Entity {type:"incident", id:$incident_id})-[ra:RELATIONSHIP]->(c:Entity {type:"component"})
                WHERE ra.type = "AFFECTS"
                MATCH (c)-[ru:RELATIONSHIP]->(a:Entity {type:"artifact"})
                WHERE ru.type = "USES"
                RETURN collect(DISTINCT a.id) AS artifacts_derived
                """
                
                derived_result = session.run(derived_artifacts_query, incident_id=incident_id)
                derived_record = derived_result.single()
                artifacts_derived = derived_record.get("artifacts_derived", []) if derived_record else []
                
                # Create stable union of direct and derived artifacts (preserve order: direct first, then derived)
                seen_all_artifacts = set(artifacts_direct)
                artifacts = list(artifacts_direct)  # Start with direct artifacts
                
                for artifact_id in artifacts_derived:
                    if artifact_id not in seen_all_artifacts:
                        artifacts.append(artifact_id)
                        seen_all_artifacts.add(artifact_id)
                
                # Log counts
                logger.info(
                    f"Explained incident {incident_id}: "
                    f"affects={len(affects)}, failure_modes={len(failure_modes)}, "
                    f"root_causes={len(root_causes)}, triggers={len(triggers)}, "
                    f"concepts={len(concepts)}, artifacts_direct={len(artifacts_direct)}, "
                    f"artifacts_derived={len(artifacts_derived)}, artifacts_total={len(artifacts)}, "
                    f"facts={len(facts)}"
                )
                
                return ExplainResponse(
                    incident_id=incident_id,
                    severity=severity,
                    affects=affects,
                    failure_modes=failure_modes,
                    root_causes=root_causes,
                    triggers=triggers,
                    concepts=concepts,
                    artifacts_direct=artifacts_direct,
                    artifacts_derived=artifacts_derived,
                    artifacts=artifacts,
                    facts=facts if include_facts else []
                )
                
        except ValueError:
            # Re-raise ValueError (incident not found)
            raise
        except Exception as e:
            logger.error(f"Error explaining incident {incident_id}: {e}", exc_info=True)
            raise

