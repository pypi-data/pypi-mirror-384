from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Atlassian
from arcade_tdk.errors import ToolExecutionError

from arcade_jira.tool_utils import system_context_utils


@tool(
    requires_auth=Atlassian(
        scopes=[
            "read:jira-user",  # /myself endpoint, accessible-resources API
        ]
    )
)
async def who_am_i(
    context: ToolContext,
) -> Annotated[
    dict[str, Any],
    "Dictionary containing the current user's information and their available Atlassian Clouds.",
]:
    """
    CALL THIS TOOL FIRST to establish user profile context.

    Get information about the currently logged-in user and their available Jira clouds/clients.
    """
    try:
        (
            clouds_available,
            current_user,
        ) = await system_context_utils.get_available_clouds_and_user_info(context)

        if not clouds_available:
            return system_context_utils.create_user_context_response(
                None, [], "No authorized Atlassian clouds found for the current user."
            )

        if not current_user:
            return system_context_utils.create_user_context_response(
                None, clouds_available, "Failed to retrieve current user information."
            )

        return system_context_utils.create_user_context_response(current_user, clouds_available)

    except Exception as e:
        raise ToolExecutionError(
            message=f"Failed to retrieve user information and available clouds: {e!s}"
        ) from e
