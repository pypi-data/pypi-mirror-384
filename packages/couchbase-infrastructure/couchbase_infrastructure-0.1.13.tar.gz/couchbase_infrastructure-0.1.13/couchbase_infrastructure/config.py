"""Configuration management for Couchbase Capella infrastructure."""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass
class CapellaConfig:
    """Configuration for Couchbase Capella infrastructure setup."""

    # Required credentials
    management_api_key: str
    organization_id: Optional[str] = None

    # API configuration
    api_base_url: str = "cloudapi.cloud.couchbase.com"

    # Project configuration
    project_name: str = "agent-app"

    # Cluster configuration
    cluster_name: str = "agent-app-cluster"
    cluster_cloud_provider: str = "aws"
    cluster_region: str = "us-east-2"
    cluster_cidr: str = "10.1.30.0/23"

    # Database configuration
    db_username: str = "agent_app_user"
    sample_bucket: str = "travel-sample"

    # AI Model configuration
    embedding_model_name: str = "nvidia/nv-embedqa-mistral-7b-v2"
    llm_model_name: str = "meta/llama3-8b-instruct"  # 3.1 requires larger instances
    ai_model_region: str = "us-east-1"

    # Model compute sizes
    # Available sizes: Extra Small (4/24), Small (4/48), Medium (48/192),
    # Large (192/320), Extra Large (192/640)
    # Note: llama-3-8b-instruct supports Extra Small, llama-3.1 requires Small+
    embedding_model_cpu: int = 4
    embedding_model_gpu_memory: int = 48
    llm_model_cpu: int = 4
    llm_model_gpu_memory: int = 48
    # Network configuration
    allowed_cidr: str = "0.0.0.0/0"

    # Timeout configuration (seconds)
    resource_timeout: Optional[int] = None  # None = wait indefinitely

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "CapellaConfig":
        """Load configuration from environment variables.

        Args:
            env_file: Optional path to .env file to load

        Returns:
            CapellaConfig instance with values from environment

        Raises:
            ValueError: If required environment variables are missing
        """
        if env_file:
            load_dotenv(env_file, override=True)
        else:
            load_dotenv(override=True)

        # Validate required environment variables
        api_key = os.getenv("MANAGEMENT_API_KEY")
        if not api_key:
            raise ValueError(
                "Missing required environment variable: MANAGEMENT_API_KEY. "
                "Please set it in your environment or .env file."
            )

        # Build config with env vars, falling back to dataclass defaults
        kwargs = {
            "management_api_key": api_key,
        }

        # Add optional overrides from environment
        if os.getenv("ORGANIZATION_ID"):
            kwargs["organization_id"] = os.getenv("ORGANIZATION_ID")
        if os.getenv("API_BASE_URL"):
            kwargs["api_base_url"] = os.getenv("API_BASE_URL")
        if os.getenv("PROJECT_NAME"):
            kwargs["project_name"] = os.getenv("PROJECT_NAME")
        if os.getenv("CLUSTER_NAME"):
            kwargs["cluster_name"] = os.getenv("CLUSTER_NAME")
        if os.getenv("CLUSTER_CLOUD_PROVIDER"):
            kwargs["cluster_cloud_provider"] = os.getenv("CLUSTER_CLOUD_PROVIDER")
        if os.getenv("CLUSTER_REGION"):
            kwargs["cluster_region"] = os.getenv("CLUSTER_REGION")
        if os.getenv("CLUSTER_CIDR"):
            kwargs["cluster_cidr"] = os.getenv("CLUSTER_CIDR")
        if os.getenv("DB_USERNAME"):
            kwargs["db_username"] = os.getenv("DB_USERNAME")
        if os.getenv("SAMPLE_BUCKET"):
            kwargs["sample_bucket"] = os.getenv("SAMPLE_BUCKET")
        if os.getenv("EMBEDDING_MODEL_NAME"):
            kwargs["embedding_model_name"] = os.getenv("EMBEDDING_MODEL_NAME")
        if os.getenv("LLM_MODEL_NAME"):
            kwargs["llm_model_name"] = os.getenv("LLM_MODEL_NAME")
        if os.getenv("AI_MODEL_REGION"):
            kwargs["ai_model_region"] = os.getenv("AI_MODEL_REGION")
        if os.getenv("EMBEDDING_MODEL_CPU"):
            kwargs["embedding_model_cpu"] = int(os.getenv("EMBEDDING_MODEL_CPU"))
        if os.getenv("EMBEDDING_MODEL_GPU_MEMORY"):
            kwargs["embedding_model_gpu_memory"] = int(os.getenv("EMBEDDING_MODEL_GPU_MEMORY"))
        if os.getenv("LLM_MODEL_CPU"):
            kwargs["llm_model_cpu"] = int(os.getenv("LLM_MODEL_CPU"))
        if os.getenv("LLM_MODEL_GPU_MEMORY"):
            kwargs["llm_model_gpu_memory"] = int(os.getenv("LLM_MODEL_GPU_MEMORY"))
        if os.getenv("RESOURCE_TIMEOUT"):
            kwargs["resource_timeout"] = int(os.getenv("RESOURCE_TIMEOUT"))

        # Note: allowed_cidr is always 0.0.0.0/0, no need to override

        return cls(**kwargs)

    def validate(self) -> None:
        """Validate configuration values.

        Raises:
            ValueError: If configuration values are invalid
        """
        if not self.management_api_key:
            raise ValueError("management_api_key is required")

        if self.embedding_model_cpu <= 0:
            raise ValueError("embedding_model_cpu must be positive")

        if self.embedding_model_gpu_memory <= 0:
            raise ValueError("embedding_model_gpu_memory must be positive")

        if self.llm_model_cpu <= 0:
            raise ValueError("llm_model_cpu must be positive")

        if self.llm_model_gpu_memory <= 0:
            raise ValueError("llm_model_gpu_memory must be positive")
