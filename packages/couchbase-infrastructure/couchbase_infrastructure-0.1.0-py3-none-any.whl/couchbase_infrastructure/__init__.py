"""Couchbase Infrastructure Automation Package.

A Python library and CLI tool for automating Couchbase Capella infrastructure setup,
including projects, clusters, databases, and AI models.
"""

__version__ = "0.1.0"
__author__ = "Couchbase"

from couchbase_infrastructure.client import CapellaClient
from couchbase_infrastructure.config import CapellaConfig
from couchbase_infrastructure.resources import (
    create_project,
    create_cluster,
    create_database_user,
    deploy_ai_model,
    load_sample_data,
)

__all__ = [
    "CapellaClient",
    "CapellaConfig",
    "create_project",
    "create_cluster",
    "create_database_user",
    "deploy_ai_model",
    "load_sample_data",
]
