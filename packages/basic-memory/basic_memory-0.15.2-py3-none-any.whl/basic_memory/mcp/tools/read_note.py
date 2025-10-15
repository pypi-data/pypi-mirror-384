"""Read note tool for Basic Memory MCP server."""

from textwrap import dedent
from typing import Optional

from loguru import logger
from fastmcp import Context

from basic_memory.mcp.async_client import get_client
from basic_memory.mcp.project_context import get_active_project
from basic_memory.mcp.server import mcp
from basic_memory.mcp.tools.search import search_notes
from basic_memory.mcp.tools.utils import call_get
from basic_memory.schemas.memory import memory_url_path
from basic_memory.utils import validate_project_path


@mcp.tool(
    description="Read a markdown note by title or permalink.",
)
async def read_note(
    identifier: str,
    project: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    context: Context | None = None,
) -> str:
    """Return the raw markdown for a note, or guidance text if no match is found.

    Finds and retrieves a note by its title, permalink, or content search,
    returning the raw markdown content including observations, relations, and metadata.

    Project Resolution:
    Server resolves projects in this order: Single Project Mode → project parameter → default project.
    If project unknown, use list_memory_projects() or recent_activity() first.

    This tool will try multiple lookup strategies to find the most relevant note:
    1. Direct permalink lookup
    2. Title search fallback
    3. Text search as last resort

    Args:
        project: Project name to read from. Optional - server will resolve using the
                hierarchy above. If unknown, use list_memory_projects() to discover
                available projects.
        identifier: The title or permalink of the note to read
                   Can be a full memory:// URL, a permalink, a title, or search text
        page: Page number for paginated results (default: 1)
        page_size: Number of items per page (default: 10)
        context: Optional FastMCP context for performance caching.

    Returns:
        The full markdown content of the note if found, or helpful guidance if not found.
        Content includes frontmatter, observations, relations, and all markdown formatting.

    Examples:
        # Read by permalink
        read_note("my-research", "specs/search-spec")

        # Read by title
        read_note("work-project", "Search Specification")

        # Read with memory URL
        read_note("my-research", "memory://specs/search-spec")

        # Read with pagination
        read_note("work-project", "Project Updates", page=2, page_size=5)

        # Read recent meeting notes
        read_note("team-docs", "Weekly Standup")

    Raises:
        HTTPError: If project doesn't exist or is inaccessible
        SecurityError: If identifier attempts path traversal

    Note:
        If the exact note isn't found, this tool provides helpful suggestions
        including related notes, search commands, and note creation templates.
    """
    async with get_client() as client:
        # Get and validate the project
        active_project = await get_active_project(client, project, context)

        # Validate identifier to prevent path traversal attacks
        # We need to check both the raw identifier and the processed path
        processed_path = memory_url_path(identifier)
        project_path = active_project.home

        if not validate_project_path(identifier, project_path) or not validate_project_path(
            processed_path, project_path
        ):
            logger.warning(
                "Attempted path traversal attack blocked",
                identifier=identifier,
                processed_path=processed_path,
                project=active_project.name,
            )
            return f"# Error\n\nIdentifier '{identifier}' is not allowed - paths must stay within project boundaries"

        # Check migration status and wait briefly if needed
        from basic_memory.mcp.tools.utils import wait_for_migration_or_return_status

        migration_status = await wait_for_migration_or_return_status(
            timeout=5.0, project_name=active_project.name
        )
        if migration_status:  # pragma: no cover
            return f"# System Status\n\n{migration_status}\n\nPlease wait for migration to complete before reading notes."
        project_url = active_project.project_url

        # Get the file via REST API - first try direct permalink lookup
        entity_path = memory_url_path(identifier)
        path = f"{project_url}/resource/{entity_path}"
        logger.info(f"Attempting to read note from Project: {active_project.name} URL: {path}")

        try:
            # Try direct lookup first
            response = await call_get(client, path, params={"page": page, "page_size": page_size})

            # If successful, return the content
            if response.status_code == 200:
                logger.info("Returning read_note result from resource: {path}", path=entity_path)
                return response.text
        except Exception as e:  # pragma: no cover
            logger.info(f"Direct lookup failed for '{path}': {e}")
            # Continue to fallback methods

        # Fallback 1: Try title search via API
        logger.info(f"Search title for: {identifier}")
        title_results = await search_notes.fn(
            query=identifier, search_type="title", project=project, context=context
        )

        # Handle both SearchResponse object and error strings
        if title_results and hasattr(title_results, "results") and title_results.results:
            result = title_results.results[0]  # Get the first/best match
            if result.permalink:
                try:
                    # Try to fetch the content using the found permalink
                    path = f"{project_url}/resource/{result.permalink}"
                    response = await call_get(
                        client, path, params={"page": page, "page_size": page_size}
                    )

                    if response.status_code == 200:
                        logger.info(f"Found note by title search: {result.permalink}")
                        return response.text
                except Exception as e:  # pragma: no cover
                    logger.info(
                        f"Failed to fetch content for found title match {result.permalink}: {e}"
                    )
        else:
            logger.info(
                f"No results in title search for: {identifier} in project {active_project.name}"
            )

        # Fallback 2: Text search as a last resort
        logger.info(f"Title search failed, trying text search for: {identifier}")
        text_results = await search_notes.fn(
            query=identifier, search_type="text", project=project, context=context
        )

        # We didn't find a direct match, construct a helpful error message
        # Handle both SearchResponse object and error strings
        if not text_results or not hasattr(text_results, "results") or not text_results.results:
            # No results at all
            return format_not_found_message(active_project.name, identifier)
        else:
            # We found some related results
            return format_related_results(active_project.name, identifier, text_results.results[:5])


def format_not_found_message(project: str | None, identifier: str) -> str:
    """Format a helpful message when no note was found."""
    return dedent(f"""
        # Note Not Found in {project}: "{identifier}"

        I couldn't find any notes matching "{identifier}". Here are some suggestions:

        ## Check Identifier Type
        - If you provided a title, try using the exact permalink instead
        - If you provided a permalink, check for typos or try a broader search

        ## Search Instead
        Try searching for related content:
        ```
        search_notes(project="{project}", query="{identifier}")
        ```

        ## Recent Activity
        Check recently modified notes:
        ```
        recent_activity(timeframe="7d")
        ```

        ## Create New Note
        This might be a good opportunity to create a new note on this topic:
        ```
        write_note(
            project="{project}",
            title="{identifier.capitalize()}",
            content='''
            # {identifier.capitalize()}

            ## Overview
            [Your content here]

            ## Observations
            - [category] [Observation about {identifier}]

            ## Relations
            - relates_to [[Related Topic]]
            ''',
            folder="notes"
        )
        ```
    """)


def format_related_results(project: str | None, identifier: str, results) -> str:
    """Format a helpful message with related results when an exact match wasn't found."""
    message = dedent(f"""
        # Note Not Found in {project}: "{identifier}"

        I couldn't find an exact match for "{identifier}", but I found some related notes:

        """)

    for i, result in enumerate(results):
        message += dedent(f"""
            ## {i + 1}. {result.title}
            - **Type**: {result.type.value}
            - **Permalink**: {result.permalink}

            You can read this note with:
            ```
            read_note(project="{project}", {result.permalink}")
            ```

            """)

    message += dedent(f"""
        ## Try More Specific Lookup
        For exact matches, try using the full permalink from one of the results above.

        ## Search For More Results
        To see more related content:
        ```
        search_notes(project="{project}", query="{identifier}")
        ```

        ## Create New Note
        If none of these match what you're looking for, consider creating a new note:
        ```
        write_note(
            project="{project}",
            title="[Your title]",
            content="[Your content]",
            folder="notes"
        )
        ```
    """)

    return message
