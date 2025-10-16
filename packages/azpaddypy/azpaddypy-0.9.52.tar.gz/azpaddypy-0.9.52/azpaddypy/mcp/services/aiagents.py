from typing import Any, Dict, List, Optional
import os
from azure.ai.projects import AIProjectClient

from .base import AzureMCPError, get_context


def list_ai_foundry_projects() -> List[Dict[str, Any]]:
    try:
        ctx = get_context()
        client = ctx.resource_client

        resources = list(client.resources.list(
            filter="resourceType eq 'Microsoft.CognitiveServices/accounts'"
        ))

        ai_projects = []
        for resource in resources:
            resource_dict = resource.as_dict()
            resource_name = resource_dict.get("name", "")
            resource_location = resource_dict.get("location", "")
            resource_id = resource_dict.get("id", "")
            resource_group = resource_id.split("/")[4] if "/" in resource_id and len(resource_id.split("/")) > 4 else ""

            properties = resource_dict.get("properties", {})
            endpoint = properties.get("endpoint", "").rstrip("/")
            ai_project_endpoint = f'{endpoint}/api/projects/{resource_name}'
            ai_projects.append({
                "name": resource_name,
                "resource_group": resource_group,
                "location": resource_location,
                "id": resource_id,
                "type": resource_dict.get("type", ""),
                "endpoint": endpoint,
                "ai_project_endpoint": ai_project_endpoint
            })

        return ai_projects
    except AzureMCPError:
        raise
    except Exception as e:
        raise AzureMCPError(f"Failed to list AI Foundry projects: {e}") from e


def _get_ai_project_client(project_endpoint: Optional[str] = None) -> AIProjectClient:
    ctx = get_context()
    ctx.ensure_initialized()

    if project_endpoint is None:
        project_endpoint = os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT")

    if not project_endpoint:
        raise AzureMCPError(
            "AZURE_AI_FOUNDRY_PROJECT_ENDPOINT environment variable is required or must be provided as parameter. "
            "Example: https://<your_ai_service_name>.services.ai.azure.com/api/projects/<your_project_name>"
        )

    try:
        client = AIProjectClient(
            endpoint=project_endpoint,
            credential=ctx.credential
        )
        return client
    except Exception as e:
        raise AzureMCPError(f"Failed to create AI Project client: {e}") from e


def list_ai_agents(ai_project_endpoint: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        client = _get_ai_project_client(ai_project_endpoint)
        agents = client.agents.list_agents()

        result = []
        for agent in agents:
            result.append({
                "id": agent.id,
                "name": agent.name,
                "model": agent.model,
                "instructions": agent.instructions,
                "created_at": agent.created_at.isoformat() if agent.created_at else None,
            })

        return result
    except AzureMCPError:
        raise
    except Exception as e:
        raise AzureMCPError(f"Failed to list AI agents: {e}") from e


def get_ai_agent(name: str, ai_project_endpoint: Optional[str] = None) -> Dict[str, Any]:
    try:
        client = _get_ai_project_client(ai_project_endpoint)
        agents = client.agents.list_agents()

        for agent in agents:
            if agent.name == name:
                return {
                    "id": agent.id,
                    "name": agent.name,
                    "model": agent.model,
                    "instructions": agent.instructions,
                    "created_at": agent.created_at.isoformat() if agent.created_at else None,
                    "available": True,
                    "project_endpoint": ai_project_endpoint or os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT")
                }

        return {
            "available": False,
            "message": f"No agent found with name: {name}"
        }
    except AzureMCPError:
        raise
    except Exception as e:
        raise AzureMCPError(f"Failed to get AI agent: {e}") from e


def create_ai_agent(
    name: str,
    model: str,
    instructions: str,
    ai_project_endpoint: Optional[str] = None
) -> Dict[str, Any]:
    try:
        client = _get_ai_project_client(ai_project_endpoint)

        agent = client.agents.create_agent(
            model=model,
            name=name,
            instructions=instructions
        )

        return {
            "id": agent.id,
            "name": agent.name,
            "model": agent.model,
            "instructions": agent.instructions,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
        }
    except AzureMCPError:
        raise
    except Exception as e:
        raise AzureMCPError(f"Failed to create AI agent: {e}") from e


def delete_ai_agent(agent_id: str, ai_project_endpoint: Optional[str] = None) -> Dict[str, Any]:
    try:
        client = _get_ai_project_client(ai_project_endpoint)

        client.agents.delete_agent(agent_id)

        return {
            "success": True,
            "message": f"Agent {agent_id} deleted successfully"
        }
    except AzureMCPError:
        raise
    except Exception as e:
        raise AzureMCPError(f"Failed to delete AI agent: {e}") from e


def invoke_ai_agent(
    agent_id: str,
    user_message: str,
    thread_id: Optional[str] = None,
    ai_project_endpoint: Optional[str] = None
) -> Dict[str, Any]:
    try:
        client = _get_ai_project_client(ai_project_endpoint)

        if thread_id is None:
            thread = client.agents.threads.create()
            thread_id = thread.id

        message = client.agents.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        run = client.agents.runs.create(
            thread_id=thread_id,
            agent_id=agent_id
        )

        while run.status in ["queued", "in_progress"]:
            import time
            time.sleep(1)
            run = client.agents.runs.get(thread_id=thread_id, run_id=run.id)

        if run.status == "completed":
            messages = client.agents.messages.list(thread_id=thread_id)

            assistant_messages = []
            for msg in messages:
                if msg.role == "assistant" and hasattr(msg, "run_id") and msg.run_id == run.id:
                    for content in msg.content:
                        if hasattr(content, "text") and hasattr(content.text, "value"):
                            assistant_messages.append(content.text.value)

            return {
                "success": True,
                "thread_id": thread_id,
                "run_id": run.id,
                "status": run.status,
                "response": "\n".join(assistant_messages)
            }
        else:
            return {
                "success": False,
                "thread_id": thread_id,
                "run_id": run.id,
                "status": run.status,
                "error": f"Run failed with status: {run.status}"
            }
    except AzureMCPError:
        raise
    except Exception as e:
        raise AzureMCPError(f"Failed to invoke AI agent: {e}") from e
