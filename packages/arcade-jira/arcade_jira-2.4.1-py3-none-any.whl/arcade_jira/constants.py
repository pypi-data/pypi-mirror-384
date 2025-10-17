import os
from enum import Enum

JIRA_BASE_URL = "https://api.atlassian.com/ex/jira"
JIRA_API_VERSION = "3"

try:
    JIRA_MAX_CONCURRENT_REQUESTS = max(1, int(os.getenv("JIRA_MAX_CONCURRENT_REQUESTS", 3)))
except Exception:
    JIRA_MAX_CONCURRENT_REQUESTS = 3

try:
    JIRA_API_REQUEST_TIMEOUT = int(os.getenv("JIRA_API_REQUEST_TIMEOUT", 30))
except Exception:
    JIRA_API_REQUEST_TIMEOUT = 30

# Board types that support sprints in Jira
BOARD_TYPES_WITH_SPRINTS = {"scrum"}

STOP_WORDS = [
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "if",
    "in",
    "into",
    "is",
    "it",
    "no",
    "not",
    "of",
    "on",
    "or",
    "such",
    "that",
    "the",
    "their",
    "then",
    "there",
    "these",
    "they",
    "this",
    "to",
    "was",
    "will",
    "with",
    "+",
    "-",
    "&",
    "|",
    "!",
    "(",
    ")",
    "{",
    "}",
    "[",
    "]",
    "^",
    "~",
    "*",
    "?",
    "\\",
    ":",
]


class IssueCommentOrderBy(Enum):
    CREATED_DATE_ASCENDING = "created_date_ascending"
    CREATED_DATE_DESCENDING = "created_date_descending"

    def to_api_value(self) -> str:
        _map: dict[IssueCommentOrderBy, str] = {
            IssueCommentOrderBy.CREATED_DATE_ASCENDING: "+created",
            IssueCommentOrderBy.CREATED_DATE_DESCENDING: "-created",
        }
        return _map[self]


class SprintState(Enum):
    FUTURE = "future"
    ACTIVE = "active"
    CLOSED = "closed"
    FUTURE_AND_ACTIVE = "future_and_active"
    FUTURE_AND_CLOSED = "future_and_closed"
    ACTIVE_AND_CLOSED = "active_and_closed"
    ALL = "all"

    def to_api_value(self) -> list[str]:
        """
        Map SprintState to Jira API representation.

        Returns:
            API value as list of strings.
        """
        mapping: dict[SprintState, list[str]] = {
            SprintState.FUTURE: ["future"],
            SprintState.ACTIVE: ["active"],
            SprintState.CLOSED: ["closed"],
            SprintState.FUTURE_AND_ACTIVE: ["future", "active"],
            SprintState.FUTURE_AND_CLOSED: ["future", "closed"],
            SprintState.ACTIVE_AND_CLOSED: ["active", "closed"],
            SprintState.ALL: ["future", "active", "closed"],
        }
        return mapping.get(self, ["active"])

    @classmethod
    def get_valid_values(cls) -> list[str]:
        """Get list of all valid string values for validation."""
        return [state.value for state in cls]


class PrioritySchemeOrderBy(Enum):
    NAME_ASCENDING = "name ascending"
    NAME_DESCENDING = "name descending"

    def to_api_value(self) -> str:
        _map: dict[PrioritySchemeOrderBy, str] = {
            PrioritySchemeOrderBy.NAME_ASCENDING: "+name",
            PrioritySchemeOrderBy.NAME_DESCENDING: "-name",
        }
        return _map[self]
