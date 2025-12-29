"""Application configuration from environment variables"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Neo4j connection settings
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j connection URI"
    )
    neo4j_user: str = Field(
        default="neo4j",
        description="Neo4j username"
    )
    neo4j_password: str = Field(
        default="password",
        description="Neo4j password"
    )
    neo4j_db: str = Field(
        default="neo4j",
        description="Neo4j database name"
    )
    
    # API settings
    api_host: str = Field(
        default="0.0.0.0",
        description="API host to bind to"
    )
    api_port: int = Field(
        default=8000,
        description="API port"
    )
    
    # Retrieval defaults
    default_max_hops: int = Field(
        default=2,
        description="Default maximum graph traversal depth"
    )
    default_max_paths: int = Field(
        default=300,
        description="Default maximum paths to return from expansion"
    )
    default_max_facts: int = Field(
        default=120,
        description="Default maximum facts to return"
    )
    default_max_anchors: int = Field(
        default=15,
        description="Default maximum anchor entities to find"
    )
    
    # Neo4j schema configuration
    relationship_mode: str = Field(
        default="property",
        description="Relationship storage mode: 'typed' (relationship labels) or 'property' (single :RELATIONSHIP label with r.type property)"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

