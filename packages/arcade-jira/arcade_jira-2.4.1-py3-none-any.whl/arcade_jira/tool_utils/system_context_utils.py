"""Utility functions for system context operations."""

from typing import Any

from arcade_tdk import ToolContext

from arcade_jira.client import JiraClient
from arcade_jira.tools.cloud import get_available_atlassian_clouds
from arcade_jira.utils import clean_user_dict


async def get_available_clouds_and_user_info(
    context: ToolContext,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """
    Get available Atlassian clouds and current user information.

    Args:
        context: Tool context for authentication

    Returns:
        Tuple of (clouds_available, current_user_info)
    """
    cloud_response = await get_available_atlassian_clouds(context)
    clouds_available = cloud_response.get("clouds_available", [])

    current_user = None
    if clouds_available:
        first_cloud = clouds_available[0]
        try:
            current_user = await get_current_user_info(
                context,
                first_cloud["atlassian_cloud_id"],
                first_cloud["atlassian_cloud_name"],
            )
        except Exception:
            current_user = None

    return clouds_available, current_user


async def get_current_user_info(
    context: ToolContext, cloud_id: str, cloud_name: str
) -> dict[str, Any]:
    """
    Retrieve current user information from a specific Jira cloud.

    Args:
        context: Tool context for authentication
        cloud_id: Atlassian cloud ID
        cloud_name: Atlassian cloud name

    Returns:
        Dictionary containing cleaned user information.

    Raises:
        Exception: If user information cannot be retrieved.
    """
    client = JiraClient(context=context, cloud_id=cloud_id)
    user_response = await client.get("myself")
    return clean_user_dict(user_response, cloud_name)


def create_user_context_response(
    current_user: dict[str, Any] | None,
    clouds_available: list[dict[str, Any]],
    error: str | None = None,
) -> dict[str, Any]:
    """
    Create a standardized response for user context operations.

    Args:
        current_user: User information dictionary or None
        clouds_available: List of available cloud dictionaries
        error: Error message if any

    Returns:
        Dictionary containing user context response.
    """
    if error:
        return {
            "error": error,
            "clouds_available": clouds_available,
        }

    return {
        "current_user": current_user,
        "clouds_available": clouds_available,
    }
