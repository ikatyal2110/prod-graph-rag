"""Neo4j database client with connection pooling and session management"""

from contextlib import contextmanager
from typing import Generator, Optional
from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable, AuthError

from app.config import settings
from app.logging import get_logger

logger = get_logger(__name__)


class Neo4jClient:
    """Neo4j client with connection pooling and session management"""
    
    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str
    ):
        """
        Initialize Neo4j client.
        
        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
            database: Neo4j database name
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self._driver: Optional[Driver] = None
        
    def connect(self) -> None:
        """Create and verify Neo4j driver connection"""
        try:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600,  # 1 hour
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
            # Verify connection
            with self._driver.session(database=self.database) as session:
                session.run("RETURN 1")
            logger.info(
                f"Connected to Neo4j at {self.uri}, database: {self.database}"
            )
        except AuthError as e:
            logger.error(f"Neo4j authentication failed: {e}")
            raise
        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self) -> None:
        """Close Neo4j driver connection"""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j driver closed")
    
    @contextmanager
    def get_session(self, database: Optional[str] = None) -> Generator[Session, None, None]:
        """
        Get a Neo4j session as a context manager.
        
        Args:
            database: Database name (defaults to configured database)
            
        Yields:
            Neo4j session
            
        Raises:
            RuntimeError: If driver is not connected
        """
        if not self._driver:
            raise RuntimeError("Neo4j driver not connected. Call connect() first.")
        
        db = database or self.database
        session = self._driver.session(database=db)
        try:
            yield session
        finally:
            session.close()
    
    def verify_connection(self) -> bool:
        """
        Verify that the connection is still alive.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            if not self._driver:
                return False
            with self.get_session() as session:
                session.run("RETURN 1")
            return True
        except Exception as e:
            logger.warning(f"Neo4j connection verification failed: {e}")
            return False


# Global client instance
_neo4j_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """
    Get or create the global Neo4j client instance.
    
    Returns:
        Neo4j client instance
    """
    global _neo4j_client
    
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            database=settings.neo4j_db
        )
        _neo4j_client.connect()
    
    return _neo4j_client

