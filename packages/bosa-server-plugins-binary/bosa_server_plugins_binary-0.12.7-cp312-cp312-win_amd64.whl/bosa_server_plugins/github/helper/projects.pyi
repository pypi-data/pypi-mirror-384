from bosa_core.cache import CacheService
from bosa_server_plugins.auth.scheme import AuthenticationScheme as AuthenticationScheme
from bosa_server_plugins.background_task.utils import is_worker_available as is_worker_available
from bosa_server_plugins.common.cache import serialize_cache_data as serialize_cache_data
from bosa_server_plugins.github.constant import GITHUB_PROJECTS_CACHE_KEY as GITHUB_PROJECTS_CACHE_KEY, GITHUB_PROJECTS_DEFAULT_TTL as GITHUB_PROJECTS_DEFAULT_TTL
from bosa_server_plugins.github.entities.project import Project as Project, ProjectItem as ProjectItem, ProjectListMeta as ProjectListMeta
from bosa_server_plugins.github.gql.project import GQLProjectListResponse as GQLProjectListResponse, get_project_list_query as get_project_list_query
from bosa_server_plugins.github.helper.common import get_sanitized_page as get_sanitized_page, get_sanitized_per_page as get_sanitized_per_page
from bosa_server_plugins.github.helper.connect import query_github_gql as query_github_gql
from bosa_server_plugins.github.tasks.get_list_project_items_task import CustomFieldFilter as CustomFieldFilter, GetItemsFromProjectParameter as GetItemsFromProjectParameter, ProjectSummary as ProjectSummary, get_items_from_project_process as get_items_from_project_process, get_items_from_project_task as get_items_from_project_task, process_items_from_project_request as process_items_from_project_request
from typing import Any

def get_items_from_project(organization: str, number: int, auth_scheme: AuthenticationScheme, force_new: bool = False, *, status: str | None = None, type_: str | None = None, page: int | None = None, per_page: int | None = None, cache_service: CacheService, created_at_from: str | None = None, created_at_to: str | None = None, updated_at_from: str | None = None, updated_at_to: str | None = None, custom_fields_filter: list[CustomFieldFilter] | None = None, summarize: bool = False, callback_urls: list[str] | None = None) -> tuple[list[ProjectItem] | ProjectSummary, dict[str, Any]] | None:
    """Get items from a GitHub Project V2.

    Args:
        organization: Organization name
        number: Project number
        auth_scheme: Authentication Scheme
        force_new: If True, bypass cache and fetch new data
        status: Optional status to filter items by
        type_: Optional type to filter items by
        page: Page number (1-based)
        per_page: Number of items per page
        cache_service: Cache service
        created_at_from: Optional start date to filter items by
        created_at_to: Optional end date to filter items by
        updated_at_from: Optional start date to filter items by
        updated_at_to: Optional end date to filter items by
        custom_fields_filter: Optional list of custom field filters
        summarize: If True, only output the summary of the project
        callback_urls: Optional list of callback URLs

    Returns:
        tuple[list[ProjectItem] | ProjectSummary, dict[str, Any]] | None: List of project
            items or project summary if summarize is True with metadata; or
            None if background task is in progress
    """
def get_projects_list(auth_scheme: AuthenticationScheme, organization: str, cache_service: CacheService = None, force_new: bool = False, *, query: str | None = None, min_permission_level: str | None = None, order_by: str | None = None, direction: str | None = None, per_page: int | None = None, cursor: str | None = None, from_last: bool | None = False) -> tuple[list[Project], ProjectListMeta]:
    """Get list of projects from a GitHub Organization.

    This function retrieves projects and uses helper functions to handle caching,
    API communication, and response formatting.

    Args:
        auth_scheme: Authentication Scheme
        organization: Organization name
        query: Query to search for (Project name/string)
        min_permission_level: Minimum permission level as string
        order_by: Field to order by
        direction: Direction to order by
        per_page: Number of items per page
        cursor: Cursor to start from
        from_last: If True, fetch from the last item
        cache_service: Cache service for caching results
        force_new: If True, bypass cache and fetch new data
    Returns:
        A tuple containing:
        - List of Project objects
        - ProjectListMeta object with pagination info and metadata
    """
