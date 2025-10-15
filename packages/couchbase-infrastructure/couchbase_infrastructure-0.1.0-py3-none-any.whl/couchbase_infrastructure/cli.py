"""CLI interface for Couchbase infrastructure automation."""

import os
import sys
from typing import Optional

import click
from rich.console import Console

from couchbase_infrastructure import __version__
from couchbase_infrastructure.client import CapellaClient
from couchbase_infrastructure.config import CapellaConfig
from couchbase_infrastructure.resources import (
    add_allowed_cidr,
    create_ai_api_key,
    create_cluster,
    create_database_user,
    create_project,
    deploy_ai_model,
    load_sample_data,
)

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="couchbase-infra")
@click.pass_context
def cli(ctx):
    """Couchbase Capella Infrastructure Automation CLI.

    Automate the setup of Couchbase Capella infrastructure including
    projects, clusters, databases, and AI models.
    """
    ctx.ensure_object(dict)


@cli.command()
@click.option(
    "--env-file",
    type=click.Path(exists=True),
    help="Path to .env file with configuration",
)
@click.option(
    "--timeout",
    type=int,
    help="Timeout in seconds for resource provisioning (default: no timeout)",
)
@click.option("--skip-models", is_flag=True, help="Skip AI model deployment")
@click.option("--skip-sample-data", is_flag=True, help="Skip loading sample data")
def setup(
    env_file: Optional[str],
    timeout: Optional[int],
    skip_models: bool,
    skip_sample_data: bool,
):
    """Run full automated infrastructure setup.

    This command will:
    1. Create or find a Capella project
    2. Deploy a free tier cluster
    3. Configure network access
    4. Load sample data (unless --skip-sample-data)
    5. Create database credentials
    6. Deploy AI models (unless --skip-models)
    7. Create API key for models

    Example:
        couchbase-infra setup --env-file .env
    """
    try:
        console.print("[bold blue]--- 🚀 Starting Automated Capella Environment Setup ---[/bold blue]\n")

        # Load configuration
        config = CapellaConfig.from_env(env_file)
        if timeout:
            config.resource_timeout = timeout
        config.validate()

        # Initialize client
        client = CapellaClient(config)
        org_id = client.get_organization_id()

        # Test API connection
        if not client.test_connection(org_id):
            console.print("\n[bold red]❌ API connection test failed. Please check your credentials.[/bold red]")
            sys.exit(1)

        # 1. Get or Create Project
        console.print("\n[bold][1/7] Finding or Creating Capella Project...[/bold]")
        project_id = create_project(client, org_id, config.project_name)

        # 2. Create and Wait for Cluster
        console.print("\n[bold][2/7] Deploying Capella Free Tier Cluster...[/bold]")
        cluster_id = create_cluster(client, org_id, project_id, config.cluster_name, config)
        cluster_check_url = f"/v4/organizations/{org_id}/projects/{project_id}/clusters/{cluster_id}"
        cluster_details = client.wait_for_resource(
            cluster_check_url, "Cluster", config.resource_timeout
        )
        cluster_conn_string = cluster_details.get("connectionString")

        # 3. Add allowed CIDR for cluster access
        console.print("\n[bold][3/7] Configuring Cluster Network Access...[/bold]")
        add_allowed_cidr(client, org_id, project_id, cluster_id, config.allowed_cidr)

        # 4. Load Sample Data
        if not skip_sample_data:
            console.print("\n[bold][4/7] Loading 'travel-sample' Dataset...[/bold]")
            load_sample_data(client, org_id, project_id, cluster_id, config.sample_bucket)
        else:
            console.print("\n[bold][4/7] Skipping sample data (--skip-sample-data)[/bold]")

        # 5. Create Database User
        console.print("\n[bold][5/7] Creating Database Credentials...[/bold]")
        db_password = create_database_user(
            client, org_id, project_id, cluster_id, config.db_username, config.sample_bucket
        )

        # 6. Deploy AI Models
        embedding_endpoint = None
        llm_endpoint = None
        api_key = None

        if not skip_models:
            console.print("\n[bold][6/7] Deploying AI Models...[/bold]")

            # Deploy Embedding Model
            console.print("   Deploying embedding model...")
            embedding_model_id = deploy_ai_model(
                client,
                org_id,
                config.embedding_model_name,
                "agent-hub-embedding-model",
                "embedding",
                config,
            )
            embedding_check_url = (
                f"/v4/organizations/{org_id}/aiServices/models/{embedding_model_id}"
            )
            embedding_details = client.wait_for_resource(
                embedding_check_url, "Embedding Model", config.resource_timeout
            )
            embedding_endpoint = embedding_details.get("connectionString", "")
            embedding_dimensions = (
                embedding_details.get("model", {}).get("config", {}).get("dimensions")
            )
            console.print(f"   Model dimensions: [cyan]{embedding_dimensions}[/cyan]")

            # Deploy LLM Model
            console.print("   Deploying LLM model...")
            llm_model_id = deploy_ai_model(
                client,
                org_id,
                config.llm_model_name,
                "agent-hub-llm-model",
                "llm",
                config,
            )
            llm_check_url = f"/v4/organizations/{org_id}/aiServices/models/{llm_model_id}"
            llm_details = client.wait_for_resource(
                llm_check_url, "LLM Model", config.resource_timeout
            )
            llm_endpoint = llm_details.get("connectionString", "")

            # 7. Create API Key for Models
            console.print("\n[bold][7/7] Creating API Key for AI Models...[/bold]")
            api_key = create_ai_api_key(client, org_id, config.ai_model_region)
        else:
            console.print("\n[bold][6/7] Skipping AI model deployment (--skip-models)[/bold]")
            console.print("[bold][7/7] Skipping API key creation[/bold]")

        # Print summary
        console.print("\n[bold green]--- ✅ SETUP COMPLETE! ---[/bold green]")
        console.print("All resources have been deployed and configured.\n")

        console.print("[bold cyan]--- 📋 Environment Variables ---[/bold cyan]")
        console.print(f"CB_CONN_STRING={cluster_conn_string}?tls_verify=none")
        console.print(f"CB_USERNAME={config.db_username}")
        console.print(f"CB_PASSWORD={db_password}")
        console.print(f"CB_BUCKET={config.sample_bucket}")

        if not skip_models and embedding_endpoint and llm_endpoint and api_key:
            console.print(f"CAPELLA_API_EMBEDDING_ENDPOINT={embedding_endpoint}")
            console.print(f"CAPELLA_API_LLM_ENDPOINT={llm_endpoint}")
            console.print(f"CAPELLA_API_EMBEDDINGS_KEY={api_key}")
            console.print(f"CAPELLA_API_LLM_KEY={api_key}")
            console.print(f"CAPELLA_API_EMBEDDING_MODEL={config.embedding_model_name}")
            console.print(f"CAPELLA_API_LLM_MODEL={config.llm_model_name}")

        console.print("\n[dim]💡 Tip: Copy these to your .env file for easy reuse[/dim]")

    except ValueError as e:
        console.print(f"\n[bold red]❌ Configuration Error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]--- ❌ SETUP FAILED ---[/bold red]")
        console.print(f"An error occurred: {e}")

        if "401" in str(e) or "Unauthorized" in str(e):
            console.print("\n[bold yellow]🔐 Authentication Error Detected:[/bold yellow]")
            console.print("1. Verify your API key is correct and not expired")
            console.print("2. Check if your current IP address is in the API key allowlist")
            console.print("3. Ensure the API key has sufficient permissions (Organization Admin role)")
            console.print("\n💡 To get your current IP: curl -s https://api.ipify.org")

        sys.exit(1)


@cli.command()
@click.option(
    "--env-file",
    type=click.Path(exists=True),
    help="Path to .env file with configuration",
)
def test_connection(env_file: Optional[str]):
    """Test API connection and credentials.

    Example:
        couchbase-infra test-connection --env-file .env
    """
    try:
        config = CapellaConfig.from_env(env_file)
        config.validate()

        client = CapellaClient(config)
        org_id = client.get_organization_id()

        if client.test_connection(org_id):
            console.print("\n[green]✅ Connection test successful![/green]")
        else:
            console.print("\n[red]❌ Connection test failed![/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    "--env-file",
    type=click.Path(exists=True),
    help="Path to .env file with configuration",
)
def list_projects(env_file: Optional[str]):
    """List all projects in the organization.

    Example:
        couchbase-infra list-projects
    """
    try:
        config = CapellaConfig.from_env(env_file)
        client = CapellaClient(config)
        org_id = client.get_organization_id()

        response = client.get(f"/v4/organizations/{org_id}/projects")

        if response.status_code == 200:
            projects = response.json().get("data", [])
            console.print(f"\n[bold]Found {len(projects)} project(s):[/bold]\n")
            for project in projects:
                console.print(f"  • [cyan]{project['name']}[/cyan] (ID: {project['id']})")
        else:
            console.print(f"[red]Failed to list projects: {response.status_code}[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    "--env-file",
    type=click.Path(exists=True),
    help="Path to .env file with configuration",
)
def list_clusters(env_file: Optional[str]):
    """List all clusters across all projects.

    Example:
        couchbase-infra list-clusters
    """
    try:
        config = CapellaConfig.from_env(env_file)
        client = CapellaClient(config)
        org_id = client.get_organization_id()

        # Get all projects
        projects_response = client.get(f"/v4/organizations/{org_id}/projects")
        if projects_response.status_code != 200:
            console.print("[red]Failed to list projects[/red]")
            sys.exit(1)

        projects = projects_response.json().get("data", [])
        console.print("\n[bold]Clusters:[/bold]\n")

        for project in projects:
            project_id = project["id"]
            project_name = project["name"]

            clusters_response = client.get(
                f"/v4/organizations/{org_id}/projects/{project_id}/clusters"
            )

            if clusters_response.status_code == 200:
                clusters = clusters_response.json().get("data", [])
                if clusters:
                    console.print(f"[cyan]{project_name}[/cyan]:")
                    for cluster in clusters:
                        status = cluster.get("status", {}).get("state", "unknown")
                        console.print(
                            f"  • {cluster['name']} (ID: {cluster['id']}, Status: {status})"
                        )

    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
