"""FastAPI application main module"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.logging import setup_logging, get_logger
from app.db import get_neo4j_client, Neo4jClient
from app.services.retrieval import RetrievalService
from app.services.explain import ExplainService
from app.services.ask import AskService
from app.models.api import QueryRequest, QueryResponse, HealthResponse, DebugInfo, ExplainRequest, ExplainResponse, AskRequest, AskResponse

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting GraphRAG API server")
    try:
        client = get_neo4j_client()
        if not client.verify_connection():
            logger.error("Neo4j connection verification failed on startup")
            raise RuntimeError("Neo4j connection failed")
        logger.info("Neo4j connection verified")
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j client: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down GraphRAG API server")
    try:
        client = get_neo4j_client()
        client.close()
    except Exception as e:
        logger.error(f"Error closing Neo4j client: {e}")


# Create FastAPI app
app = FastAPI(
    title="GraphRAG API",
    description="Production-grade GraphRAG retrieval API over Neo4j",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_retrieval_service(neo4j_client: Neo4jClient = Depends(get_neo4j_client)) -> RetrievalService:
    """Dependency to get retrieval service"""
    return RetrievalService(neo4j_client)


def get_explain_service(neo4j_client: Neo4jClient = Depends(get_neo4j_client)) -> ExplainService:
    """Dependency to get explain service"""
    return ExplainService(neo4j_client)


def get_ask_service(
    neo4j_client: Neo4jClient = Depends(get_neo4j_client),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    explain_service: ExplainService = Depends(get_explain_service)
) -> AskService:
    """Dependency to get ask service"""
    return AskService(neo4j_client, retrieval_service, explain_service)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    try:
        client = get_neo4j_client()
        if client.verify_connection():
            logger.debug(f"Health check: connected to {client.database} at {client.uri}")
            return HealthResponse(status="ok")
        else:
            return HealthResponse(status="degraded")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
):
    """
    GraphRAG query endpoint.
    
    Finds anchor entities from question, expands subgraph, extracts facts.
    
    Args:
        request: Query request with question and parameters
        retrieval_service: Retrieval service dependency
        
    Returns:
        Query response with anchors, facts, evidence, and stats
    """
    try:
        logger.info(f"Processing query: {request.question[:100]}...")
        
        # Perform retrieval
        anchors, facts, evidence, stats, debug_info = retrieval_service.retrieve(
            question=request.question,
            max_hops=request.max_hops,
            max_paths=request.max_paths,
            max_facts=request.max_facts,
            max_anchors=6,  # Default max anchors
            max_incidents=request.max_incidents,
            debug=request.debug
        )
        
        # Build debug info if requested
        debug = None
        if request.debug and debug_info:
            debug = DebugInfo(**debug_info)
        
        # Build response
        response = QueryResponse(
            question=request.question,
            anchors=anchors,
            facts=facts,
            evidence=evidence,
            stats=stats,
            debug=debug
        )
        
        logger.info(
            f"Query completed: {len(anchors)} anchors, {len(facts)} facts, "
            f"{len(evidence.incident_ids)} incidents"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@app.post("/explain", response_model=ExplainResponse)
async def explain_incident(
    request: ExplainRequest,
    explain_service: ExplainService = Depends(get_explain_service)
):
    """
    Explain an incident by retrieving its relationships and categorizing them.
    
    Args:
        request: Explain request with incident_id and include_facts flag
        explain_service: Explain service dependency
        
    Returns:
        ExplainResponse with categorized relationships
        
    Raises:
        HTTPException: 404 if incident not found, 500 on error
    """
    try:
        logger.info(f"Explain request for incident: {request.incident_id}")
        response = explain_service.explain_incident(
            incident_id=request.incident_id,
            include_facts=request.include_facts
        )
        return response
        
    except ValueError as e:
        # Incident not found
        logger.warning(f"Incident not found: {request.incident_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error explaining incident {request.incident_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to explain incident: {str(e)}")


@app.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    ask_service: AskService = Depends(get_ask_service)
):
    """
    Ask a question and get a deterministic grounded answer.
    
    Combines /query and /explain logic to produce a narrative answer.
    
    Args:
        request: Ask request with question and parameters
        ask_service: Ask service dependency
        
    Returns:
        AskResponse with answer, evidence, key facts, and incident cards
        
    Raises:
        HTTPException: 500 on error
    """
    try:
        logger.info(f"Ask request: {request.question[:100]}...")
        response = ask_service.ask(
            question=request.question,
            max_incidents=request.max_incidents,
            max_facts=request.max_facts
        )
        logger.info(
            f"Ask completed: {len(response.evidence.incident_ids)} incidents, "
            f"{len(response.key_facts)} key facts, {len(response.incident_cards)} incident cards"
        )
        return response
        
    except Exception as e:
        logger.error(f"Ask processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ask processing failed: {str(e)}")


@app.get("/debug/stats")
async def debug_stats(neo4j_client: Neo4jClient = Depends(get_neo4j_client)):
    """
    Debug endpoint to verify database connection and data.
    Returns counts from the live database.
    """
    try:
        stats = {}
        
        with neo4j_client.get_session() as session:
            # Total nodes
            result = session.run("MATCH (n) RETURN count(n) AS count")
            stats["total_nodes"] = result.single()["count"]
            
            # Total relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            stats["total_relationships"] = result.single()["count"]
            
            # Entity nodes
            result = session.run("MATCH (e:Entity) RETURN count(e) AS count")
            stats["entity_nodes"] = result.single()["count"]
            
            # Test lookup for "kubelet"
            result = session.run('MATCH (e:Entity {id: "kubelet"}) RETURN count(e) AS count')
            stats["kubelet_entity_exists"] = result.single()["count"] > 0
            
            # Database info
            stats["database"] = neo4j_client.database
            stats["neo4j_uri"] = neo4j_client.uri
            
            # Entity types breakdown
            result = session.run("MATCH (e:Entity) RETURN e.type AS type, count(e) AS count ORDER BY count DESC")
            stats["entity_types"] = {record["type"]: record["count"] for record in result}
            
            # Relationship types (check both modes)
            # Try property mode first
            result = session.run("MATCH ()-[r:RELATIONSHIP]->() RETURN r.type AS type, count(r) AS count ORDER BY count DESC LIMIT 20")
            prop_rels = list(result)
            if prop_rels:
                stats["relationship_types_property_mode"] = {record["type"]: record["count"] for record in prop_rels}
            else:
                # Try typed relationships
                result = session.run("MATCH ()-[r]->() WITH type(r) AS rel_type, count(r) AS count RETURN rel_type, count ORDER BY count DESC LIMIT 20")
                typed_rels = list(result)
                stats["relationship_types_typed_mode"] = {record["rel_type"]: record["count"] for record in typed_rels}
        
        return stats
        
    except Exception as e:
        logger.error(f"Debug stats failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stats: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "GraphRAG API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "query": "/query",
            "explain": "/explain",
            "ask": "/ask",
            "debug_stats": "/debug/stats"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False
    )

