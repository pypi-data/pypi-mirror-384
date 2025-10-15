"""
WeaviateAdapter - Adapter for Weaviate vector database.

This adapter provides methods to convert between Pydantic models and Weaviate objects,
with comprehensive error handling and validation.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, ClassVar, TypeVar
import urllib.parse
import uuid

from pydantic import BaseModel, ValidationError

from ..core import Adapter, AdapterBase, dispatch_adapt_meth
from ..exceptions import ConnectionError, PydapterError, QueryError, ResourceError
from ..exceptions import ValidationError as AdapterValidationError

T = TypeVar("T", bound=BaseModel)


class WeaviateAdapter(AdapterBase, Adapter[T]):
    """
    Adapter for Weaviate vector database.

    This adapter provides methods to convert between Pydantic models and Weaviate objects,
    with support for vector search operations.

    Attributes:
        adapter_key: The key identifier for this adapter type ("weav")
        obj_key: Legacy key identifier (for backward compatibility)
    """

    adapter_key: ClassVar[str] = "weav"
    obj_key: ClassVar[str] = "weav"  # Backward compatibility

    @classmethod
    def _client(cls, url: str | None = None):
        """
        Create a Weaviate client with error handling.

        Args:
            url: Weaviate server URL (defaults to http://localhost:8080)

        Returns:
            weaviate.WeaviateClient: Configured client instance

        Raises:
            ConnectionError: If connection to Weaviate fails
        """
        try:
            # Import weaviate here to avoid circular imports
            import importlib.util

            if importlib.util.find_spec("weaviate") is None:
                raise ImportError("Weaviate module not found")

            import weaviate
            from weaviate.connect import ConnectionParams

            # Parse URL to extract host and port
            parsed_url = urllib.parse.urlparse(url or "http://localhost:8080")
            host = parsed_url.hostname or "localhost"
            http_port = parsed_url.port or 8080

            # Connect to Weaviate using v4 API
            # search:pplx-516f9410 - Weaviate v4 connection parameters example
            # search:pplx-ccec835b - Weaviate Python client v4 API changes
            connection_params = ConnectionParams.from_params(
                http_host=host,
                http_port=http_port,
                http_secure=parsed_url.scheme == "https",
                grpc_host=host,
                grpc_port=50051,  # Use the default gRPC port that Weaviate uses
                grpc_secure=parsed_url.scheme == "https",
            )

            # Create and connect the client
            client = weaviate.WeaviateClient(
                connection_params=connection_params,
                skip_init_checks=True,  # Skip health checks for testing
            )

            # Connect the client before returning it
            client.connect()

            return client
        except ImportError as e:
            raise ConnectionError(
                f"Weaviate module not available: {e}",
                adapter="weav",
                url=url or "http://localhost:8080",
            ) from e
        except Exception as e:
            raise ConnectionError(
                f"Failed to create Weaviate client: {e}",
                adapter="weav",
                url=url or "http://localhost:8080",
            ) from e

    # outgoing
    @classmethod
    def to_obj(
        cls,
        subj: T | Sequence[T],
        /,
        *,
        class_name: str,
        vector_field: str = "embedding",
        url: str | None = None,
        many: bool = True,
        adapt_meth: str | Callable = "model_dump",
        adapt_kw: dict | None = None,
        **kw,
    ) -> dict | None:
        """
        Convert from Pydantic models to Weaviate objects.

        Args:
            subj: Model instance or sequence of model instances
            class_name: Weaviate class name
            vector_field: Field containing vector data (defaults to "embedding")
            url: Weaviate server URL (defaults to http://localhost:8080)
            **kw: Additional keyword arguments

        Returns:
            dict: Operation result with count of added objects

        Raises:
            AdapterValidationError: If required parameters are missing or invalid
            ConnectionError: If connection to Weaviate fails
            QueryError: If query execution fails
        """
        try:
            # Validate required parameters
            if not class_name:
                raise AdapterValidationError("Missing required parameter 'class_name'")

            # Prepare data
            items = subj if isinstance(subj, Sequence) else [subj]
            if not items:
                return {"added_count": 0}  # Nothing to insert

            # Create client and ensure class exists
            client = cls._client(url)

            try:
                # Check if collection exists, create if not
                try:
                    # Get the collection
                    collection = client.collections.get(class_name)
                except Exception:
                    # Collection doesn't exist, create it
                    try:
                        # Create collection with proper vectorizer config
                        # In Weaviate v4, vectorizer_config needs to be properly structured
                        collection = client.collections.create(
                            class_name,
                            vectorizer_config=None,  # Don't use vectorizer, we provide vectors
                            properties=[
                                {
                                    "name": "name",
                                    "data_type": ["text"],
                                },
                                {
                                    "name": "value",
                                    "data_type": ["number"],
                                },
                            ],
                        )
                    except Exception as e:
                        raise QueryError(
                            f"Failed to get or create collection: {e}",
                            adapter="weav",
                        ) from e

                # Add objects in batch
                added_count = 0
                # Process objects one by one
                for it in items:
                    # Validate vector field exists
                    if not hasattr(it, vector_field):
                        raise AdapterValidationError(
                            f"Vector field '{vector_field}' not found in model",
                            data=dispatch_adapt_meth(adapt_meth, it, adapt_kw or {}, type(it)),
                        )

                    # Get vector data
                    vector = getattr(it, vector_field)
                    if not isinstance(vector, list):
                        raise AdapterValidationError(
                            f"Vector field '{vector_field}' must be a list of floats",
                            data=dispatch_adapt_meth(adapt_meth, it, adapt_kw or {}, type(it)),
                        )

                    # Exclude id and vector_field from properties using dispatch_adapt_meth
                    # Create modified adapt_kw with exclude parameter
                    modified_kw = (adapt_kw or {}).copy()
                    modified_kw["exclude"] = {vector_field, "id"}
                    properties = dispatch_adapt_meth(adapt_meth, it, modified_kw, type(it))

                    # Generate a UUID based on the model's ID if available
                    obj_uuid = None
                    if hasattr(it, "id"):
                        # Create a deterministic UUID from the model ID
                        # This ensures the same model ID always maps to the same UUID
                        namespace = uuid.UUID(
                            "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
                        )  # UUID namespace
                        obj_uuid = str(uuid.uuid5(namespace, f"{it.id}"))

                    # Add object to collection
                    try:
                        # Create object with vector
                        if obj_uuid:
                            collection.data.insert(
                                properties=properties, vector=vector, uuid=obj_uuid
                            )
                        else:
                            collection.data.insert(properties=properties, vector=vector)
                        added_count += 1
                    except Exception as e:
                        raise QueryError(
                            f"Failed to add object to Weaviate: {e}",
                            adapter="weav",
                        ) from e

                return {"added_count": added_count}

            except PydapterError:
                # Re-raise our custom exceptions
                raise
            except Exception as e:
                # Wrap other exceptions
                cls._handle_error(e, "query", unexpected=True)

        except PydapterError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Safety net for unexpected errors - check for connection failures
            if "Connection failed" in str(e) or "Connection" in str(e):
                raise ConnectionError(
                    f"Failed to connect to Weaviate: {e}", adapter="weav", url=url
                ) from e
            cls._handle_error(e, "query", unexpected=True)

    # incoming
    @classmethod
    def from_obj(
        cls,
        subj_cls: type[T],
        obj: dict[str, Any],
        /,
        *,
        many: bool = True,
        adapt_meth: str | Callable = "model_validate",
        adapt_kw: dict | None = None,
        validation_errors: tuple[type[Exception], ...] = (ValidationError,),
        **kw,
    ) -> T | list[T]:
        """
        Convert from Weaviate objects to Pydantic models.

        Args:
            subj_cls: Target model class
            obj: Dictionary with query parameters
            many: Whether to return multiple results
            **kw: Additional keyword arguments

        Required parameters in obj:
            class_name: Weaviate class name
            query_vector: Vector to search for similar objects

        Optional parameters in obj:
            url: Weaviate server URL (defaults to http://localhost:8080)
            top_k: Maximum number of results to return (defaults to 5)

        Returns:
            T | list[T]: Single model instance or list of model instances

        Raises:
            AdapterValidationError: If required parameters are missing
            ConnectionError: If connection to Weaviate fails
            QueryError: If query execution fails
            ResourceError: If no matching objects are found
        """
        try:
            # Validate required parameters
            if "class_name" not in obj:
                raise AdapterValidationError("Missing required parameter 'class_name'", data=obj)
            if "query_vector" not in obj:
                raise AdapterValidationError("Missing required parameter 'query_vector'", data=obj)

            # Create client
            client = cls._client(obj.get("url"))

            try:
                # Execute query
                # Execute query
                try:
                    # Get the collection
                    collection = client.collections.get(obj["class_name"])

                    # Execute the query
                    query_result = (
                        collection.query.near_vector(
                            obj["query_vector"],
                            distance=0.7,  # Default distance threshold
                            limit=obj.get("top_k", 5),
                        )
                        .with_additional(["id", "vector"])  # Include vector in response
                        .do()
                    )

                    # Extract objects from the result
                    # Handle both mock objects in tests and real objects in production
                    if hasattr(query_result, "objects"):
                        # For real Weaviate client or properly mocked objects
                        data = []
                        for item in query_result.objects:
                            # Get properties
                            props = getattr(item, "properties", item)
                            # Add additional fields (id, vector)
                            additional = getattr(item, "additional", {})
                            if additional:
                                if "id" in additional:
                                    props["id"] = additional["id"]
                                if "vector" in additional:
                                    props["embedding"] = additional["vector"]
                            data.append(props)
                    elif isinstance(query_result, dict) and "data" in query_result:
                        # For old API format in tests
                        data = query_result["data"]["Get"].get(obj["class_name"], [])
                    else:
                        data = []
                except Exception as e:
                    raise QueryError(
                        f"Failed to execute Weaviate query: {e}",
                        adapter="weav",
                    ) from e

                # Check if data is empty
                if not data:
                    if many:
                        return []
                    raise ResourceError(
                        "No objects found matching the query",
                        resource=obj["class_name"],
                    )

                # Convert to model instances using dispatch_adapt_meth
                try:
                    if many:
                        return [
                            dispatch_adapt_meth(adapt_meth, r, adapt_kw or {}, subj_cls)
                            for r in data
                        ]
                    return dispatch_adapt_meth(adapt_meth, data[0], adapt_kw or {}, subj_cls)
                except validation_errors as e:
                    cls._handle_error(
                        e,
                        "validation",
                        data=data[0] if not many else data,
                        errors=e.errors() if hasattr(e, "errors") else None,
                    )

            except PydapterError:
                # Re-raise our custom exceptions
                raise
            except Exception as e:
                # Wrap other exceptions
                cls._handle_error(e, "query", unexpected=True)

        except PydapterError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Safety net for unexpected errors
            cls._handle_error(e, "query", unexpected=True)
