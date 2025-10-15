"""
AsyncNeo4jAdapter - Asynchronous adapter for Neo4j graph database.

This adapter provides asynchronous access to Neo4j using the AsyncGraphDatabase.
It follows the AsyncAdapter protocol and provides comprehensive error handling and
resource management.
"""

from __future__ import annotations

from collections.abc import Sequence
import re

import neo4j
from neo4j import AsyncGraphDatabase
import neo4j.exceptions
from pydantic import ValidationError

from ..async_core import AsyncAdapter, T
from ..exceptions import ConnectionError, QueryError, ResourceError
from ..exceptions import ValidationError as AdapterValidationError

# T is already imported from async_core


class AsyncNeo4jAdapter(AsyncAdapter[T]):
    """
    Asynchronous adapter for Neo4j graph database.

    This adapter provides methods to convert between Pydantic models and Neo4j nodes,
    with full support for asynchronous operations.
    """

    obj_key = "async_neo4j"

    # Class variable for driver factory - makes testing easier
    _driver_factory = AsyncGraphDatabase.driver

    def __init__(self, url=None, auth=None, **kwargs):
        """Initialize the adapter with connection parameters.

        Args:
            url: Neo4j connection URL
            auth: Optional authentication tuple (username, password)
            **kwargs: Additional keyword arguments
        """
        self.url = url
        self.auth = auth
        self.kwargs = kwargs
        self._driver = None
        self._session = None

    @classmethod
    def set_driver_factory(cls, factory):
        """Set the driver factory for testing purposes."""
        cls._driver_factory = factory

    @classmethod
    def reset_driver_factory(cls):
        """Reset the driver factory to the default."""
        cls._driver_factory = AsyncGraphDatabase.driver

    @classmethod
    async def _create_driver(cls, url: str, auth=None) -> neo4j.AsyncDriver:
        """Create a Neo4j async driver with error handling.

        Args:
            url: Neo4j connection URL
            auth: Optional authentication tuple (username, password)

        Returns:
            neo4j.AsyncDriver: Configured Neo4j async driver

        Raises:
            ConnectionError: If connection to Neo4j fails
        """
        try:
            if auth:
                return cls._driver_factory(url, auth=auth)
            else:
                return cls._driver_factory(url)
        except neo4j.exceptions.ServiceUnavailable as e:
            raise ConnectionError(
                f"Neo4j service unavailable: {e}", adapter="async_neo4j", url=url
            ) from e
        except neo4j.exceptions.AuthError as e:
            raise ConnectionError(
                f"Neo4j authentication failed: {e}", adapter="async_neo4j", url=url
            ) from e
        except Exception as e:
            raise ConnectionError(
                f"Failed to create Neo4j driver: {e}", adapter="async_neo4j", url=url
            ) from e

    @classmethod
    def _validate_cypher(cls, cypher: str) -> None:
        """Basic validation for Cypher queries to prevent injection.

        Args:
            cypher: Cypher query string to validate

        Raises:
            QueryError: If the query contains potentially unsafe patterns
        """
        # Check for unescaped backticks in label names
        if re.search(r"`[^`]*`[^`]*`", cypher):
            raise QueryError(
                "Invalid Cypher query: Possible injection in label name",
                query=cypher,
                adapter="async_neo4j",
            )

    # incoming
    @classmethod
    async def from_obj(
        cls,
        subj_cls: type[T],
        obj: dict,
        /,
        *,
        many=True,
        adapt_meth: str = "model_validate",
        adapt_kw: dict | None = None,
        **kw,
    ):
        """
        Convert from Neo4j nodes to Pydantic models asynchronously.

        Args:
            subj_cls: Target model class
            obj: Dictionary with query parameters
            many: Whether to return multiple results
            **kw: Additional keyword arguments

        Required parameters in obj:
            url: Neo4j connection URL

        Optional parameters in obj:
            auth: Authentication tuple (username, password)
            label: Node label (defaults to model class name)
            where: Cypher WHERE clause

        Returns:
            T | list[T]: Single model instance or list of model instances

        Raises:
            AdapterValidationError: If required parameters are missing
            ConnectionError: If connection to Neo4j fails
            QueryError: If query execution fails
            ResourceError: If no matching nodes are found

        search:exa-v1w2x3y4 - Async pattern for Neo4j query execution
        search:pplx-z5a6b7c8 - Error handling in async Neo4j operations
        """
        try:
            # Validate required parameters
            if "url" not in obj:
                raise AdapterValidationError("Missing required parameter 'url'", data=obj)

            # Create driver
            auth = obj.get("auth")
            driver = await cls._create_driver(obj["url"], auth=auth)

            # Prepare Cypher query
            label = obj.get("label", subj_cls.__name__)
            where = f"WHERE {obj['where']}" if "where" in obj else ""
            cypher = f"MATCH (n:`{label}`) {where} RETURN n"

            # Validate Cypher query
            cls._validate_cypher(cypher)

            # Execute query
            try:
                # Use the driver directly without nested context managers
                session = driver.session()
                try:
                    try:
                        # Execute the query - session.run() returns Result immediately (not awaitable)
                        result = session.run(cypher)
                        # Process the results
                        rows = []
                        async for record in result:
                            # Extract the node properties from the 'n' field
                            try:
                                # Try to access the 'n' field (standard for from_obj queries)
                                node = record["n"]
                                if hasattr(node, "_properties"):
                                    rows.append(dict(node._properties))
                                else:
                                    rows.append(dict(node))
                            except (KeyError, TypeError):
                                # Fallback: convert entire record to dict
                                row_dict = {}
                                try:
                                    for key in record:
                                        value = record[key]
                                        if hasattr(value, "_properties"):
                                            row_dict[key] = dict(value._properties)
                                        else:
                                            row_dict[key] = value
                                    rows.append(row_dict)
                                except AttributeError:
                                    # If record doesn't have keys(), treat as simple value
                                    rows.append({"n": record})
                    except neo4j.exceptions.CypherSyntaxError as e:
                        raise QueryError(
                            f"Neo4j Cypher syntax error: {e}",
                            query=cypher,
                            adapter="async_neo4j",
                        ) from e
                    except neo4j.exceptions.ClientError as e:
                        if "not found" in str(e).lower():
                            raise ResourceError(
                                f"Neo4j resource not found: {e}",
                                resource=label,
                            ) from e
                        raise QueryError(
                            f"Neo4j client error: {e}",
                            query=cypher,
                            adapter="async_neo4j",
                        ) from e
                    except Exception as e:
                        raise QueryError(
                            f"Error executing Neo4j query: {e}",
                            query=cypher,
                            adapter="async_neo4j",
                        ) from e

                    # Handle empty result set
                    if not rows:
                        if many:
                            return []
                        raise ResourceError(
                            "No nodes found matching the query",
                            resource=label,
                            where=obj.get("where", ""),
                        )

                    # Convert rows to model instances
                    try:
                        if many:
                            return [
                                getattr(subj_cls, adapt_meth)(r, **(adapt_kw or {})) for r in rows
                            ]
                        return getattr(subj_cls, adapt_meth)(rows[0], **(adapt_kw or {}))
                    except ValidationError as e:
                        raise AdapterValidationError(
                            f"Validation error: {e}",
                            data=rows[0] if not many else rows,
                            errors=e.errors(),
                        ) from e
                finally:
                    if session:
                        try:
                            await session.close()
                        except Exception:
                            # Ignore errors during session close
                            pass

            except (ConnectionError, QueryError, ResourceError, AdapterValidationError):
                # Re-raise our custom exceptions
                raise
            except Exception as e:
                # Wrap other exceptions
                raise QueryError(
                    f"Error in Neo4j query: {e}",
                    adapter="async_neo4j",
                ) from e

        except (ConnectionError, QueryError, ResourceError, AdapterValidationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Wrap other exceptions
            raise QueryError(
                f"Unexpected error in async Neo4j adapter: {e}", adapter="async_neo4j"
            ) from e

    # outgoing
    @classmethod
    async def to_obj(
        cls,
        subj: T | Sequence[T],
        /,
        *,
        url,
        auth=None,
        label=None,
        merge_on="id",
        many: bool = True,
        adapt_meth: str = "model_dump",
        adapt_kw: dict | None = None,
        **kw,
    ):
        """
        Convert from Pydantic models to Neo4j nodes asynchronously.

        Args:
            subj: Model instance or sequence of model instances
            url: Neo4j connection URL
            auth: Optional authentication tuple (username, password)
            label: Node label (defaults to model class name)
            merge_on: Property to use for MERGE operation (defaults to "id")
            **kw: Additional keyword arguments

        Returns:
            dict: Operation result with count of merged nodes

        Raises:
            AdapterValidationError: If required parameters are missing
            ConnectionError: If connection to Neo4j fails
            QueryError: If query execution fails

        search:pplx-d9e0f1g2 - Neo4j MERGE operation best practices
        search:exa-h3i4j5k6 - Async batch operations with Neo4j
        """
        try:
            # Validate required parameters
            if not url:
                raise AdapterValidationError("Missing required parameter 'url'")
            if not merge_on:
                raise AdapterValidationError("Missing required parameter 'merge_on'")

            # Prepare data
            items = subj if isinstance(subj, Sequence) else [subj]
            if not items:
                return None  # Nothing to insert

            # Get label from first item if not provided
            label = label or items[0].__class__.__name__

            # Create driver
            driver = await cls._create_driver(url, auth=auth)

            try:
                # Use the driver directly without nested context managers
                session = driver.session()
                try:
                    results = []
                    for it in items:
                        props = getattr(it, adapt_meth)(**(adapt_kw or {}))

                        # Check if merge_on property exists
                        if merge_on not in props:
                            raise AdapterValidationError(
                                f"Merge property '{merge_on}' not found in model",
                                data=props,
                            )

                        # Prepare and validate Cypher query
                        cypher = f"MERGE (n:`{label}` {{{merge_on}: $val}}) SET n += $props"
                        cls._validate_cypher(cypher)

                        # Execute query
                        try:
                            # Execute the query - session.run() returns Result immediately (not awaitable)
                            result = session.run(cypher, val=props[merge_on], props=props)
                            # Consume the result to ensure it's executed
                            summary = await result.consume()
                            # Add to results
                            results.append(summary)
                        except neo4j.exceptions.CypherSyntaxError as e:
                            raise QueryError(
                                f"Neo4j Cypher syntax error: {e}",
                                query=cypher,
                                adapter="async_neo4j",
                            ) from e
                        except neo4j.exceptions.ConstraintError as e:
                            raise QueryError(
                                f"Neo4j constraint violation: {e}",
                                query=cypher,
                                adapter="async_neo4j",
                            ) from e
                        except Exception as e:
                            raise QueryError(
                                f"Error executing Neo4j query: {e}",
                                query=cypher,
                                adapter="async_neo4j",
                            ) from e

                    return {"merged_count": len(results)}
                finally:
                    if session:
                        try:
                            await session.close()
                        except Exception:
                            # Ignore errors during session close
                            pass

            except (ConnectionError, QueryError, AdapterValidationError):
                # Re-raise our custom exceptions
                raise
            except Exception as e:
                # Wrap other exceptions
                raise QueryError(
                    f"Error in Neo4j operation: {e}",
                    adapter="async_neo4j",
                ) from e

        except (ConnectionError, QueryError, AdapterValidationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Wrap other exceptions
            raise QueryError(
                f"Unexpected error in async Neo4j adapter: {e}", adapter="async_neo4j"
            ) from e

    async def __aenter__(self):
        """Async context manager entry.

        Returns:
            self: The adapter instance

        Raises:
            ConnectionError: If connection to Neo4j fails
        """
        if not self.url:
            raise ConnectionError("URL is required for Neo4j connection", adapter="async_neo4j")

        self._driver = await self._create_driver(self.url, auth=self.auth)
        try:
            # For the mock tests, we don't need to await the session
            self._session = self._driver.session()
            return self
        except Exception as e:
            # Clean up driver if session creation fails
            if self._driver:
                await self._driver.close()
            raise e

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        if self._session:
            try:
                await self._session.close()
            except Exception:
                # Ignore errors during session close
                pass

        if self._driver:
            try:
                await self._driver.close()
            except Exception:
                # Ignore errors during driver close
                pass

    async def query(self, cypher, **params):
        """Execute a Cypher query and return the results.

        Args:
            cypher: Cypher query string
            **params: Query parameters

        Returns:
            list: List of query results as dictionaries

        Raises:
            QueryError: If the query execution fails
        """
        if not self._session:
            raise QueryError(
                "No active session. Use AsyncNeo4jAdapter as a context manager.",
                adapter="async_neo4j",
            )

        # Validate Cypher query
        self._validate_cypher(cypher)

        try:
            # Execute the query - session.run() returns Result immediately (not awaitable)
            result = self._session.run(cypher, **params)

            # Process the results - handle arbitrary query result structures
            rows = []
            async for record in result:
                # Convert record to dictionary with all returned values
                row_dict = {}
                for key in record:
                    value = record[key]
                    # Handle Neo4j nodes/relationships by extracting properties
                    if hasattr(value, "_properties"):
                        row_dict[key] = dict(value._properties)
                    elif hasattr(value, "items"):  # Dict-like
                        row_dict[key] = dict(value)
                    else:
                        row_dict[key] = value
                rows.append(row_dict)

            return rows
        except neo4j.exceptions.CypherSyntaxError as e:
            raise QueryError(
                f"Neo4j Cypher syntax error: {e}",
                query=cypher,
                adapter="async_neo4j",
            ) from e
        except Exception as e:
            raise QueryError(
                f"Error executing Neo4j query: {e}",
                query=cypher,
                adapter="async_neo4j",
            ) from e
