"""
YouTrack Search API client with advanced search capabilities.
"""

from typing import Any

from youtrack_rocket_mcp.api.client import YouTrackClient
from youtrack_rocket_mcp.api.schemas import CustomFieldSettingDict, IssueDict
from youtrack_rocket_mcp.api.types import CustomFieldData


class SearchClient:
    """Client for advanced search operations in YouTrack."""

    @staticmethod
    def format_custom_fields(custom_fields: list[Any]) -> dict[str, str | None]:
        """
        Format custom fields from array to dictionary {name: value}.

        Args:
            custom_fields: List of custom field objects

        Returns:
            Dictionary mapping field names to their values
        """
        result = {}
        for field in custom_fields:
            name = field.get('name')
            if name:
                value = field.get('value')
                if value:
                    # Extract actual value from complex objects
                    if isinstance(value, dict):
                        # Check if it's an empty type object (like {"$type": "StateBundleElement"})
                        if len(value) == 1 and '$type' in value:
                            # This is an empty value, the field type is set but no actual value
                            actual_value = None
                        else:
                            # For objects like User, State, etc., try to get the most meaningful value
                            actual_value = (
                                value.get('name')
                                or value.get('login')
                                or value.get('text')
                                or value.get('localizedName')
                                or (str(value.get('id', '')) if value.get('id') else None)
                            )
                    elif isinstance(value, list):
                        # For multi-value fields
                        if len(value) > 0:
                            actual_value = ', '.join(
                                v.get('name', str(v)) if isinstance(v, dict) else str(v) for v in value
                            )
                        else:
                            actual_value = None
                    else:
                        actual_value = str(value) if value else None
                    result[name] = actual_value
                else:
                    result[name] = None
        return result

    def __init__(self, client: YouTrackClient):
        """
        Initialize the Search API client.

        Args:
            client: The YouTrack API client
        """
        self.client = client

    async def search_issues(
        self,
        query: str,
        fields: list[str] | None = None,
        limit: int = 10,
        offset: int = 0,
        sort_by: str | None = None,
        sort_order: str | None = None,
        custom_fields: list[str] | None = None,
    ) -> list[IssueDict]:
        """
        Search for issues with advanced query capabilities.

        Args:
            query: The YouTrack query string
            fields: List of fields to include in the response (default: all fields)
            limit: Maximum number of issues to return
            offset: Offset for pagination
            sort_by: Field to sort by (e.g., 'created', 'updated', 'priority')
            sort_order: Sort order ('asc' or 'desc')
            custom_fields: List of custom field names to include

        Returns:
            List of matching issues with requested fields
        """
        # Base set of fields to retrieve
        default_fields = [
            'id',
            'idReadable',
            'summary',
            'description',
            'created',
            'updated',
            'resolved',
            'priority',
            'project(id,name,shortName)',
            'reporter(id,login,name)',
            'assignee(id,login,name)',
        ]

        # Combine default fields with requested fields
        requested_fields = default_fields + fields if fields else default_fields

        # Add custom fields if requested
        if custom_fields:
            # Build the customFields part with specific field names
            cf_string = ','.join(['customFields(id,name,value)' for _ in custom_fields])
            requested_fields.append(cf_string)
        else:
            # By default, include all custom fields
            requested_fields.append('customFields(id,name,value)')

        # Build the fields parameter
        fields_param = ','.join(requested_fields)

        # Build params dictionary
        params = {'query': query, '$top': limit, '$skip': offset, 'fields': fields_param}

        # Add sort parameters if provided
        if sort_by:
            params['$sort'] = sort_by
            if sort_order and sort_order.lower() in ('asc', 'desc'):
                params['$sortOrder'] = sort_order.lower()

        # Make the API request
        issues = await self.client.get('issues', params=params, schema=list[IssueDict])

        # Format custom fields for each issue
        for issue in issues:
            if 'customFields' in issue:
                issue['custom_fields'] = self.format_custom_fields(issue['customFields'])
                # Remove original customFields - keep only formatted version
                del issue['customFields']

        return issues

    async def search_with_custom_field_values(
        self, query: str, custom_field_values: CustomFieldData, limit: int = 10
    ) -> list[IssueDict]:
        """
        Search for issues with specific custom field values.

        Args:
            query: The base YouTrack query string
            custom_field_values: Dictionary mapping custom field names to values
            limit: Maximum number of issues to return

        Returns:
            List of matching issues
        """
        # Build query with custom field conditions
        enhanced_query = query

        for field_name, field_value in custom_field_values.items():
            if field_value is not None:
                # Handle different types of values
                if isinstance(field_value, bool):
                    value_str = 'true' if field_value else 'false'
                elif isinstance(field_value, int | float):
                    value_str = str(field_value)
                elif isinstance(field_value, list):
                    # For multi-value fields, we use 'in' operator
                    values = ', '.join([f'"{val}"' for val in field_value])
                    enhanced_query += f' {field_name} in ({values})'
                    continue
                else:
                    # String values need to be quoted
                    value_str = f'"{field_value}"'

                # Add the condition to the query
                enhanced_query += f' {field_name}: {value_str}'

        # Call the search_issues method with the enhanced query
        return await self.search_issues(enhanced_query, limit=limit)

    async def search_with_filter(
        self,
        project: str | None = None,
        author: str | None = None,
        assignee: str | None = None,
        state: str | None = None,
        priority: str | None = None,
        text: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        custom_fields: CustomFieldData | None = None,
        limit: int = 10,
    ) -> list[IssueDict]:
        """
        Search for issues using a structured filter approach.

        Args:
            project: Project ID or name
            author: Issue author (reporter) login or name
            assignee: Issue assignee login or name
            state: Issue state (e.g., "Open", "Resolved")
            priority: Issue priority
            text: Text to search in summary and description
            created_after: Issues created after this date (YYYY-MM-DD)
            created_before: Issues created before this date (YYYY-MM-DD)
            updated_after: Issues updated after this date (YYYY-MM-DD)
            updated_before: Issues updated before this date (YYYY-MM-DD)
            custom_fields: Dictionary mapping custom field names to values
            limit: Maximum number of issues to return

        Returns:
            List of matching issues
        """
        # Build query based on provided filters
        query_parts = []

        if project:
            query_parts.append(f'project: "{project}"')

        if author:
            query_parts.append(f'reporter: "{author}"')

        if assignee:
            if assignee.lower() == 'unassigned':
                query_parts.append('assignee: Unassigned')
            else:
                query_parts.append(f'assignee: "{assignee}"')

        if state:
            query_parts.append(f'State: "{state}"')

        if priority:
            query_parts.append(f'Priority: "{priority}"')

        if text:
            # Search in summary and description
            query_parts.append(f'summary: "{text}" description: "{text}"')

        if created_after:
            query_parts.append(f'created: {created_after} ..')

        if created_before:
            query_parts.append(f'created: .. {created_before}')

        if updated_after:
            query_parts.append(f'updated: {updated_after} ..')

        if updated_before:
            query_parts.append(f'updated: .. {updated_before}')

        # Combine all parts into a single query
        base_query = ' '.join(query_parts)

        # If custom fields are provided, use the specialized method
        if custom_fields:
            return await self.search_with_custom_field_values(base_query, custom_fields, limit)
        return await self.search_issues(base_query, limit=limit)

    async def get_available_custom_fields(self, project_id: str | None = None) -> list[CustomFieldSettingDict]:
        """
        Get all available custom fields, optionally for a specific project.

        Args:
            project_id: Optional project ID to get fields for a specific project

        Returns:
            List of custom fields with their properties
        """
        if project_id:
            # Get custom fields for a specific project
            endpoint = f'admin/projects/{project_id}/customFields'
        else:
            # Get all custom fields in the system
            endpoint = 'admin/customFieldSettings/customFields'

        fields = 'id,name,localizedName,fieldType(id,name),isPrivate,isPublic,aliases'
        params = {'fields': fields}

        return await self.client.get(endpoint, params=params, schema=list[CustomFieldSettingDict])
