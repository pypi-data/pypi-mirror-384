from typing import Annotated, cast

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Atlassian

from arcade_jira.client import JiraClient
from arcade_jira.utils import resolve_cloud_id


@tool(requires_auth=Atlassian(scopes=["read:jira-work", "read:jira-user"]))
async def get_transition_by_id(
    context: ToolContext,
    issue: Annotated[str, "The ID or key of the issue"],
    transition_id: Annotated[str, "The ID of the transition"],
    atlassian_cloud_id: Annotated[
        str | None,
        "The ID of the Atlassian Cloud to use (defaults to None). If not provided and the user has "
        "a single cloud authorized, the tool will use that. Otherwise, an error will be raised.",
    ] = None,
) -> Annotated[dict, "The transition data"]:
    """Get a transition by its ID."""
    if not transition_id:
        return {"error": "The transition ID is required."}
    if not transition_id.isdigit():
        return {"error": "The transition ID must be a numeric string."}

    atlassian_cloud_id = await resolve_cloud_id(context, atlassian_cloud_id)
    client = JiraClient(context=context, cloud_id=atlassian_cloud_id)
    response = await client.get(
        f"/issue/{issue}/transitions",
        params={
            "transitionId": transition_id,
        },
    )
    transitions = response["transitions"]

    if len(transitions) == 0:
        return {
            "error": (
                f"No transition found for the issue '{issue}' with ID '{transition_id}'. "
                "To get all transitions available for the issue, use the "
                f"`Jira.{get_transitions_available_for_issue.__tool_name__}` tool."
            ),
        }

    if len(transitions) == 1:
        return {"transition": transitions[0]}

    return {
        "error": f"Multiple transitions found for the issue '{issue}' with ID '{transition_id}'.",
        "transitions": transitions,
    }


@tool(requires_auth=Atlassian(scopes=["read:jira-work", "read:jira-user"]))
async def get_transitions_available_for_issue(
    context: ToolContext,
    issue: Annotated[str, "The ID or key of the issue"],
    atlassian_cloud_id: Annotated[
        str | None,
        "The ID of the Atlassian Cloud to use (defaults to None). If not provided and the user has "
        "a single cloud authorized, the tool will use that. Otherwise, an error will be raised.",
    ] = None,
) -> Annotated[dict, "The transitions available and the issue's current status"]:
    """Get the transitions available for an existing Jira issue."""
    from arcade_jira.tools.issues import get_issue_by_id  # Avoid circular import

    atlassian_cloud_id = await resolve_cloud_id(context, atlassian_cloud_id)
    client = JiraClient(context=context, cloud_id=atlassian_cloud_id)
    issue_data = await get_issue_by_id(
        context=context,
        issue=issue,
        atlassian_cloud_id=atlassian_cloud_id,
    )
    if issue_data.get("error"):
        return cast(dict, issue_data)
    response = await client.get(
        f"/issue/{issue_data['issue']['id']}/transitions",
        params={
            "expand": "transitions.fields",
        },
    )
    return {
        "issue": {
            "id": issue_data["issue"]["id"],
            "key": issue_data["issue"]["key"],
            "current_status": issue_data["issue"]["status"],
        },
        "transitions_available": response["transitions"],
    }


@tool(
    requires_auth=Atlassian(
        scopes=[
            "read:jira-work",  # Needed to get the transitions available for the issue
            "write:jira-work",  # Needed to transition the issue
        ],
    ),
)
async def get_transition_by_status_name(
    context: ToolContext,
    issue: Annotated[str, "The ID or key of the issue"],
    transition: Annotated[str, "The name of the transition status"],
    atlassian_cloud_id: Annotated[
        str | None,
        "The ID of the Atlassian Cloud to use (defaults to None). If not provided and the user has "
        "a single cloud authorized, the tool will use that. Otherwise, an error will be raised.",
    ] = None,
) -> Annotated[dict, "The transition data, including screen fields available"]:
    """Get a transition available for an issue by the transition name.

    The response will contain screen fields available for the transition, if any.
    """
    transitions = await get_transitions_available_for_issue(
        context=context,
        issue=issue,
        atlassian_cloud_id=atlassian_cloud_id,
    )
    for available_transition in transitions["transitions_available"]:
        if available_transition["name"].casefold() == transition.casefold():
            return {"issue": issue, "transition": available_transition}
    return {
        "error": f"Transition '{transition}' not found for the issue '{issue}'",
        "transitions_available": transitions["transitions_available"],
    }


@tool(
    requires_auth=Atlassian(
        scopes=[
            "read:jira-work",  # Needed to get the transition ID by name
            "write:jira-work",  # Needed to transition the issue
            "read:jira-user",
        ],
    ),
)
async def transition_issue_to_new_status(
    context: ToolContext,
    issue: Annotated[str, "The ID or key of the issue"],
    transition: Annotated[
        str,
        "The transition to perform. Provide the transition ID or its name (case insensitive).",
    ],
    atlassian_cloud_id: Annotated[
        str | None,
        "The ID of the Atlassian Cloud to use (defaults to None). If not provided and the user has "
        "a single cloud authorized, the tool will use that. Otherwise, an error will be raised.",
    ] = None,
) -> Annotated[dict, "The updated issue"]:
    """Transition a Jira issue to a new status."""
    atlassian_cloud_id = await resolve_cloud_id(context, atlassian_cloud_id)
    client = JiraClient(context=context, cloud_id=atlassian_cloud_id)

    # Try to get the transition by ID first
    response = await get_transition_by_id(
        context=context,
        issue=issue,
        transition_id=transition,
        atlassian_cloud_id=atlassian_cloud_id,
    )

    # If the transition is not found by ID, try to get it by name
    if response.get("error"):
        response = await get_transition_by_status_name(
            context=context,
            issue=issue,
            transition=transition,
            atlassian_cloud_id=atlassian_cloud_id,
        )
        if response.get("error"):
            return cast(dict, response)

    transition_id = response["transition"]["id"]
    transition_name = response["transition"]["name"]

    # The /issue/issue_id/transitions endpoint returns a 204 No Content in case of success
    await client.post(
        f"/issue/{issue}/transitions",
        json_data={
            "transition": {"id": transition_id},
        },
    )

    return {
        "status": "success",
        "message": f"Issue '{issue}' successfully transitioned to '{transition_name}'.",
    }
