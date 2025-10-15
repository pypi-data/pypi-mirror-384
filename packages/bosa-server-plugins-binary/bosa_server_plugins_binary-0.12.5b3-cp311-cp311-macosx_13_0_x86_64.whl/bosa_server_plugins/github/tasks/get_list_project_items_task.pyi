import abc
from _typeshed import Incomplete
from abc import ABC, abstractmethod
from bosa_core.cache import CacheService as CacheService
from bosa_server_plugins.auth.bearer import BearerTokenAuthentication as BearerTokenAuthentication
from bosa_server_plugins.auth.scheme import AuthenticationScheme as AuthenticationScheme
from bosa_server_plugins.common.cache import deserialize_cache_data as deserialize_cache_data
from bosa_server_plugins.common.callback import with_callbacks as with_callbacks
from bosa_server_plugins.github.constant import GITHUB_PROJECTS_DEFAULT_TTL as GITHUB_PROJECTS_DEFAULT_TTL
from bosa_server_plugins.github.entities.project import ProjectItem as ProjectItem
from bosa_server_plugins.github.gql.project import GQLProjectItemFieldValue as GQLProjectItemFieldValue, PROJECT_ITEM_FRAGMENT as PROJECT_ITEM_FRAGMENT
from bosa_server_plugins.github.helper.common import parse_date as parse_date
from bosa_server_plugins.github.helper.connect import query_github_gql as query_github_gql
from enum import Enum
from pydantic import BaseModel, RootModel
from typing import Any, Literal

PROJECT_ITEMS_QUERY: Incomplete

class FilterType(str, Enum):
    """Filter type enum for discriminated union."""
    DATE_RANGE = 'date_range'
    STRING = 'string'
    STRING_LIST = 'string_list'
    NUMBER = 'number'
    NUMBER_LIST = 'number_list'
    NUMBER_RANGE = 'number_range'

class BaseCustomFieldFilter(BaseModel, ABC, metaclass=abc.ABCMeta):
    """Base class for all custom field filters."""
    field_name: str
    @abstractmethod
    def apply(self, item: ProjectItem) -> bool:
        """Apply the filter to the item.

        Args:
            item: The item to apply the filter to.

        Returns:
            True if the item passes the filter, False otherwise.
        """

class DateRangeFilter(BaseCustomFieldFilter):
    """Filter items by a date range.

    Args:
        from_date: Start date of the range
        to_date: End date of the range
    """
    type: Literal[FilterType.DATE_RANGE]
    from_date: str | None
    to_date: str | None
    def apply(self, item: ProjectItem) -> bool:
        """Apply the filter to the item.

        Args:
            item: The item to apply the filter to.
        """

class StringFilter(BaseCustomFieldFilter):
    """Filter items by string value."""
    type: Literal[FilterType.STRING]
    value: str
    ignore_case: bool | None
    def apply(self, item: ProjectItem) -> bool:
        """Apply the filter to the item.

        Args:
            item: The item to apply the filter to.
        """

class StringListFilter(BaseCustomFieldFilter):
    """Filter items by a list of string values."""
    type: Literal[FilterType.STRING_LIST]
    values: list[str]
    ignore_case: bool | None
    def apply(self, item: ProjectItem) -> bool:
        """Apply the filter to the item.

        Args:
            item: The item to apply the filter to.
        """

class NumberFilter(BaseCustomFieldFilter):
    """Filter items by a number.

    Args:
        value: Value to filter by
    """
    type: Literal[FilterType.NUMBER]
    value: float
    def apply(self, item: ProjectItem) -> bool:
        """Apply the filter to the item.

        Args:
            item: The item to apply the filter to.
        """

class NumberListFilter(BaseCustomFieldFilter):
    """Filter items by a list of numbers.

    Args:
        values: List of values to filter by
    """
    type: Literal[FilterType.NUMBER_LIST]
    values: list[float]
    def apply(self, item: ProjectItem) -> bool:
        """Apply the filter to the item.

        Args:
            item: The item to apply the filter to.
        """

class NumberRangeFilter(BaseCustomFieldFilter):
    """Filter items by a number range. If none of the value is provided, will always return True.

    Args:
        from_value: Start value of the range. If not provided, will ignore the lower bound.
        to_value: End value of the range. If not provided, will ignore the upper bound.
    """
    type: Literal[FilterType.NUMBER_RANGE]
    from_value: float | None
    to_value: float | None
    def apply(self, item: ProjectItem) -> bool:
        """Apply the filter to the item.

        Args:
            item: The item to apply the filter to.

        Returns:
            True if the item passes the filter, False otherwise.
            Will always return True if both from_value and to_value are not provided.
        """

FilterUnion: Incomplete

class CustomFieldFilter(RootModel[FilterUnion]):
    '''Root model for all filter types that uses discriminated union.

    This class uses the \'type\' field to determine which filter to instantiate.
    Example usage in a request:

    ```json
    {
      "filters": [
        {
          "type": "date_range",
          "field_name": "due_date",
          "from_date": "2023-01-01T00:00:00Z",
          "to_date": "2023-12-31T23:59:59Z"
        },
        {
          "type": "string_list",
          "field_name": "status",
          "values": ["open", "in progress"]
        }
      ]
    }
    ```
    '''
    def apply(self, item: ProjectItem) -> bool:
        """Apply the filter to the item."""
    @property
    def field_name(self) -> str:
        """Get the field name."""

class GetItemsFromProjectParameter(BaseModel):
    """Get items from project parameter."""
    status: str | None
    type_: str | None
    created_at_from: str | None
    created_at_to: str | None
    updated_at_from: str | None
    updated_at_to: str | None
    custom_fields_filter: list[CustomFieldFilter] | None
    summarize: bool
    callback_urls: list[str] | None

class ProjectSummaryField(BaseModel):
    """Project summary field."""
    field_name: str
    summaries: dict[str, Any]

class ProjectSummary(BaseModel):
    """Project summary."""
    total_items: int
    summary_fields: list[ProjectSummaryField]

def get_items_from_project_task(self, organization: str, number: int, auth_schema_key: str, item_key: str, parameter: dict, page: int, per_page: int):
    """Get items from a GitHub Project V2 and process with parameters.

    Args:
        self: Celery task instance
        organization: Organization name
        number: Project number
        auth_schema_key: Authentication scheme key
        item_key: Item cache key
        parameter: Get items from project parameter
        page: Page number
        per_page: Number of items per page

    Returns:
        Dictionary with fetched count and status
    """
def get_items_from_project_process(organization: str, number: int, auth_scheme: AuthenticationScheme, cache_service: CacheService, key: str) -> list[ProjectItem]:
    """Internal function to get items from a GitHub Project V2 with caching.

    Args:
        organization: Organization name
        number: Project number
        auth_scheme: Authentication Scheme
        cache_service: Cache service
        key: Cache key

    Returns:
        List of project items
    """
def process_items_from_project_request(items: list[ProjectItem], parameter: GetItemsFromProjectParameter, page: int, per_page: int) -> tuple[list[ProjectItem] | ProjectSummary, dict[str, Any]]:
    """Process filter items from project request.

    Args:
        items: List of project items
        parameter: Get items from project parameter
        page: Page number
        per_page: Number of items per page

    Returns:
        Tuple of list of project items or project summary and pagination metadata
    """
def send_get_project_items_callbacks(data: tuple[list[ProjectItem] | ProjectSummary, dict[str, Any]], callback_urls: list[str]):
    """Process get items from project requests.

    Args:
        data: Tuple of list of project items or project summary and pagination metadata
        callback_urls: List of callback URLs

    Returns:
        Tuple of list of project items or project summary and pagination metadata
    """
