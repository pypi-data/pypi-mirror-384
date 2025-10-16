# Couchbase Infrastructure

A Python CLI tool and library for automating Couchbase Capella infrastructure setup, including projects, clusters, databases, and AI models.

## Features

- 🚀 **One-Command Setup**: Deploy complete Capella infrastructure with a single command
- 🔧 **CLI & Library**: Use as a command-line tool or import as a Python library
- 🤖 **AI Model Support**: Automated deployment of embedding and LLM models
- 📦 **Sample Data Loading**: Automatically load sample datasets like travel-sample
- 🔐 **Credential Management**: Secure API key and database user management
- ⚙️ **Configurable**: Customize via environment variables or config files
- 🎨 **Rich Output**: Beautiful CLI with progress indicators and colored output

## Installation

### From PyPI

```bash
pip install couchbase-infrastructure
```

### From Source

```bash
git clone https://github.com/couchbase/couchbase-infrastructure.git
cd couchbase-infrastructure
pip install -e .
```

## Prerequisites

Before using this tool, you need:

1. **Couchbase Capella Account**: Sign up at [cloud.couchbase.com](https://cloud.couchbase.com)
2. **Management API Key**: Generate from Capella Console → Settings → API Keys
   - Required permissions: Organization Admin
3. **Organization ID** (optional, will auto-detect if not provided)

### Get Your Management API Key

1. Log in to Couchbase Capella Console
2. Navigate to Settings → API Keys
3. Create a new API key with Organization Admin permissions
4. Add your current IP address to the allowlist
5. Copy the API key (you'll only see it once!)

## Quick Start

### 1. Set Environment Variables

Create a `.env` file:

```bash
# Required
MANAGEMENT_API_KEY=your_api_key_here

# Optional (will auto-detect if not provided)
ORGANIZATION_ID=your_org_id_here

# Optional customizations
PROJECT_NAME=Agent-Hub-Project
CLUSTER_NAME=agent-hub-cluster
DB_USERNAME=agent_app_user
EMBEDDING_MODEL_NAME=nvidia/nv-embedqa-mistral-7b-v2
LLM_MODEL_NAME=meta/llama-3.1-8b-instruct
```

### 2. Run Full Setup

```bash
couchbase-infra setup --env-file .env
```

This will:
1. ✅ Create or find a Capella project
2. ✅ Deploy a free tier cluster
3. ✅ Configure network access (allowlist)
4. ✅ Load travel-sample dataset
5. ✅ Create database credentials
6. ✅ Deploy embedding and LLM models
7. ✅ Create API key for models

## CLI Usage

### Test Connection

Test your API credentials:

```bash
couchbase-infra test-connection --env-file .env
```

### Full Setup

Deploy complete infrastructure:

```bash
# Basic setup
couchbase-infra setup --env-file .env

# Skip AI model deployment
couchbase-infra setup --env-file .env --skip-models

# Skip sample data loading
couchbase-infra setup --env-file .env --skip-sample-data

# Set custom timeout (in seconds)
couchbase-infra setup --env-file .env --timeout 3600
```

### List Resources

```bash
# List all projects
couchbase-infra list-projects

# List all clusters
couchbase-infra list-clusters
```

### Get Help

```bash
# General help
couchbase-infra --help

# Command-specific help
couchbase-infra setup --help
```

## Programmatic Usage

Use as a Python library in your own scripts:

```python
from couchbase_infrastructure import (
    CapellaClient,
    CapellaConfig,
    create_project,
    create_cluster,
    deploy_ai_model,
)

# Load configuration from environment
config = CapellaConfig.from_env(".env")

# Initialize client
client = CapellaClient(config)
org_id = client.get_organization_id()

# Test connection
if client.test_connection(org_id):
    print("Connected successfully!")

# Create project
project_id = create_project(client, org_id, "My Project")

# Create cluster
cluster_id = create_cluster(client, org_id, project_id, "my-cluster", config)

# Deploy AI model
model_id = deploy_ai_model(
    client,
    org_id,
    "nvidia/nv-embedqa-mistral-7b-v2",
    "my-embedding-model",
    "embedding",
    config,
)
```

## Configuration Options

All options can be set via environment variables:

### Required
- `MANAGEMENT_API_KEY`: Your Capella Management API key

### Optional
- `ORGANIZATION_ID`: Organization ID (auto-detected if not provided)
- `API_BASE_URL`: API base URL (default: cloudapi.cloud.couchbase.com)

### Project & Cluster
- `PROJECT_NAME`: Project name (default: Agent-Hub-Project)
- `CLUSTER_NAME`: Cluster name (default: agent-hub-flight-cluster)
- `CLUSTER_CLOUD_PROVIDER`: Cloud provider (default: aws)
- `CLUSTER_REGION`: AWS region (default: us-east-2)
- `CLUSTER_CIDR`: CIDR block (default: 10.1.30.0/23)

### Database
- `DB_USERNAME`: Database username (default: agent_app_user)
- `SAMPLE_BUCKET`: Sample bucket name (default: travel-sample)

### AI Models
- `EMBEDDING_MODEL_NAME`: Embedding model (default: nvidia/nv-embedqa-mistral-7b-v2)
- `LLM_MODEL_NAME`: LLM model (default: meta/llama-3.1-8b-instruct)
- `AI_MODEL_REGION`: AI model region (default: us-east-1)
- `EMBEDDING_MODEL_CPU`: Embedding CPU cores (default: 4)
- `EMBEDDING_MODEL_GPU_MEMORY`: Embedding GPU memory GB (default: 24)
- `LLM_MODEL_CPU`: LLM CPU cores (default: 4)
- `LLM_MODEL_GPU_MEMORY`: LLM GPU memory GB (default: 48)

### Network & Timeouts
- `ALLOWED_CIDR`: Allowed CIDR for cluster access (default: 0.0.0.0/0)
- `RESOURCE_TIMEOUT`: Timeout in seconds (default: no timeout)

## Model Compute Sizes

Available compute sizes for AI models:

| Size | CPU (vCPUs) | GPU Memory (GB) |
|------|-------------|-----------------|
| Extra Small | 4 | 24 |
| Small | 4 | 48 |
| Medium | 48 | 192 |
| Large | 192 | 320 |
| Extra Large | 192 | 640 |

Note: Extra Large may not be available in sandbox environments.

## Troubleshooting

### Authentication Failed (401)

1. Verify your API key is correct and not expired
2. Check if your current IP is in the API key allowlist
3. Ensure the API key has Organization Admin permissions

Get your current IP:
```bash
curl -s https://api.ipify.org
```

### Free Tier Cluster Already Exists

Capella free tier allows only one cluster. The tool will automatically detect and use the existing cluster.

### Timeout Issues

For slower provisioning, increase the timeout:
```bash
couchbase-infra setup --timeout 7200  # 2 hours
```

Or remove timeout completely (wait indefinitely) by not setting the `--timeout` flag.

### Connection Issues

Test your connection first:
```bash
couchbase-infra test-connection
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/couchbase/couchbase-infrastructure.git
cd couchbase-infrastructure

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black couchbase_infrastructure/
ruff check couchbase_infrastructure/

# Type check
mypy couchbase_infrastructure/
```

### Project Structure

```
couchbase-infrastructure/
├── couchbase_infrastructure/
│   ├── __init__.py       # Package initialization
│   ├── cli.py            # CLI interface
│   ├── client.py         # API client
│   ├── config.py         # Configuration
│   └── resources.py      # Resource management
├── tests/                # Unit tests
├── pyproject.toml        # Package metadata
└── README.md             # Documentation
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/couchbase/couchbase-infrastructure/issues)
- **Documentation**: [Couchbase Capella Docs](https://docs.couchbase.com/cloud/)
- **Community**: [Couchbase Forums](https://forums.couchbase.com/)

## Related Projects

- [Couchbase Python SDK](https://github.com/couchbase/couchbase-python-client)
- [Agent Catalog](https://github.com/couchbaselabs/agent-catalog)
- [Capella Management API](https://docs.couchbase.com/cloud/management-api-guide/)

## Changelog

### 0.1.0 (2024-10-15)

- Initial release
- Full infrastructure automation
- CLI and library support
- AI model deployment
- Sample data loading
