import os
import logging
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

from ...core.errors import APIKeyVerificationError

logger = logging.getLogger("Lucidic")


def get_dataset(
    dataset_id: str,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get a dataset by ID with all its items.
    
    Args:
        dataset_id: The ID of the dataset to retrieve (required).
        api_key: API key for authentication. If not provided, will use the LUCIDIC_API_KEY environment variable.
        agent_id: Agent ID. If not provided, will use the LUCIDIC_AGENT_ID environment variable.
    
    Returns:
        A dictionary containing the dataset information including:
        - dataset_id: The dataset ID
        - name: Dataset name
        - description: Dataset description
        - tags: List of tags
        - created_at: Creation timestamp
        - updated_at: Last update timestamp
        - num_items: Number of items in the dataset
        - items: List of dataset items
    
    Raises:
        APIKeyVerificationError: If API key or agent ID is missing or invalid.
        ValueError: If dataset_id is not provided.
    """
    load_dotenv()
    
    # Validation
    if not dataset_id:
        raise ValueError("Dataset ID is required")
    
    # Get credentials
    if api_key is None:
        api_key = os.getenv("LUCIDIC_API_KEY", None)
        if api_key is None:
            raise APIKeyVerificationError(
                "Make sure to either pass your API key into get_dataset() or set the LUCIDIC_API_KEY environment variable."
            )
    
    if agent_id is None:
        agent_id = os.getenv("LUCIDIC_AGENT_ID", None)
        if agent_id is None:
            raise APIKeyVerificationError(
                "Lucidic agent ID not specified. Make sure to either pass your agent ID into get_dataset() or set the LUCIDIC_AGENT_ID environment variable."
            )
    
    # Get HTTP client
    from ..init import get_http
    from ...core.config import SDKConfig
    from ...api.client import HttpClient
    
    http = get_http()
    if not http:
        # Create a new HTTP client if needed
        config = SDKConfig.from_env(api_key=api_key, agent_id=agent_id)
        http = HttpClient(config)
    
    # Make request to get dataset
    response = http.get('getdataset', {'dataset_id': dataset_id})
    
    logger.info(f"Retrieved dataset {dataset_id} with {response.get('num_items', 0)} items")
    return response


def get_dataset_items(
    dataset_id: str,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to get just the items from a dataset.

    Args:
        dataset_id: The ID of the dataset to retrieve items from (required).
        api_key: API key for authentication. If not provided, will use the LUCIDIC_API_KEY environment variable.
        agent_id: Agent ID. If not provided, will use the LUCIDIC_AGENT_ID environment variable.

    Returns:
        A list of dataset items, where each item contains:
        - datasetitem_id: The item ID
        - name: Item name
        - description: Item description
        - tags: List of tags
        - input: Input data for the item
        - expected_output: Expected output data
        - metadata: Additional metadata
        - created_at: Creation timestamp

    Raises:
        APIKeyVerificationError: If API key or agent ID is missing or invalid.
        ValueError: If dataset_id is not provided.
    """
    dataset = get_dataset(dataset_id, api_key, agent_id)
    return dataset.get('items', [])


def list_datasets(
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List all datasets for the agent.

    Args:
        api_key: API key for authentication. If not provided, will use the LUCIDIC_API_KEY environment variable.
        agent_id: Agent ID. If not provided, will use the LUCIDIC_AGENT_ID environment variable.

    Returns:
        A dictionary containing:
        - num_datasets: Number of datasets
        - datasets: List of dataset summaries with dataset_id and name

    Raises:
        APIKeyVerificationError: If API key or agent ID is missing or invalid.
    """
    from ..init import get_resources, get_http
    from ...core.config import SDKConfig
    from ...api.client import HttpClient

    # Get or create resources
    resources = get_resources()
    if not resources or 'datasets' not in resources:
        load_dotenv()

        # Get credentials
        if api_key is None:
            api_key = os.getenv("LUCIDIC_API_KEY", None)
            if api_key is None:
                raise APIKeyVerificationError(
                    "Make sure to either pass your API key or set the LUCIDIC_API_KEY environment variable."
                )

        if agent_id is None:
            agent_id = os.getenv("LUCIDIC_AGENT_ID", None)

        config = SDKConfig.from_env(api_key=api_key, agent_id=agent_id)
        http = HttpClient(config)
        from ...api.resources.dataset import DatasetResource
        resources = {'datasets': DatasetResource(http)}

    return resources['datasets'].list_datasets(agent_id)


def create_dataset(
    name: str,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    suggested_flag_config: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new dataset.

    Args:
        name: Dataset name (must be unique per agent)
        description: Optional dataset description
        tags: Optional list of tags
        suggested_flag_config: Optional flag configuration
        api_key: API key for authentication
        agent_id: Agent ID

    Returns:
        A dictionary containing dataset_id

    Raises:
        APIKeyVerificationError: If API key or agent ID is missing or invalid.
    """
    from ..init import get_resources, get_http
    from ...core.config import SDKConfig
    from ...api.client import HttpClient

    # Get or create resources
    resources = get_resources()
    if not resources or 'datasets' not in resources:
        load_dotenv()

        if api_key is None:
            api_key = os.getenv("LUCIDIC_API_KEY", None)
            if api_key is None:
                raise APIKeyVerificationError(
                    "Make sure to either pass your API key or set the LUCIDIC_API_KEY environment variable."
                )

        if agent_id is None:
            agent_id = os.getenv("LUCIDIC_AGENT_ID", None)

        config = SDKConfig.from_env(api_key=api_key, agent_id=agent_id)
        http = HttpClient(config)
        from ...api.resources.dataset import DatasetResource
        resources = {'datasets': DatasetResource(http)}

    return resources['datasets'].create_dataset(name, description, tags, suggested_flag_config, agent_id)


def update_dataset(
    dataset_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    suggested_flag_config: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update dataset metadata.

    Args:
        dataset_id: Dataset UUID to update
        name: New name (optional)
        description: New description (optional)
        tags: New tags (optional)
        suggested_flag_config: New flag config (optional)
        api_key: API key for authentication
        agent_id: Agent ID

    Returns:
        Updated dataset data

    Raises:
        APIKeyVerificationError: If API key or agent ID is missing or invalid.
    """
    from ..init import get_resources, get_http
    from ...core.config import SDKConfig
    from ...api.client import HttpClient

    # Get or create resources
    resources = get_resources()
    if not resources or 'datasets' not in resources:
        load_dotenv()

        if api_key is None:
            api_key = os.getenv("LUCIDIC_API_KEY", None)
            if api_key is None:
                raise APIKeyVerificationError(
                    "Make sure to either pass your API key or set the LUCIDIC_API_KEY environment variable."
                )

        if agent_id is None:
            agent_id = os.getenv("LUCIDIC_AGENT_ID", None)

        config = SDKConfig.from_env(api_key=api_key, agent_id=agent_id)
        http = HttpClient(config)
        from ...api.resources.dataset import DatasetResource
        resources = {'datasets': DatasetResource(http)}

    kwargs = {}
    if name is not None:
        kwargs['name'] = name
    if description is not None:
        kwargs['description'] = description
    if tags is not None:
        kwargs['tags'] = tags
    if suggested_flag_config is not None:
        kwargs['suggested_flag_config'] = suggested_flag_config

    return resources['datasets'].update_dataset(dataset_id, **kwargs)


def delete_dataset(
    dataset_id: str,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Delete a dataset and all its items.

    Args:
        dataset_id: Dataset UUID to delete
        api_key: API key for authentication
        agent_id: Agent ID

    Returns:
        Success message

    Raises:
        APIKeyVerificationError: If API key or agent ID is missing or invalid.
    """
    from ..init import get_resources, get_http
    from ...core.config import SDKConfig
    from ...api.client import HttpClient

    # Get or create resources
    resources = get_resources()
    if not resources or 'datasets' not in resources:
        load_dotenv()

        if api_key is None:
            api_key = os.getenv("LUCIDIC_API_KEY", None)
            if api_key is None:
                raise APIKeyVerificationError(
                    "Make sure to either pass your API key or set the LUCIDIC_API_KEY environment variable."
                )

        if agent_id is None:
            agent_id = os.getenv("LUCIDIC_AGENT_ID", None)

        config = SDKConfig.from_env(api_key=api_key, agent_id=agent_id)
        http = HttpClient(config)
        from ...api.resources.dataset import DatasetResource
        resources = {'datasets': DatasetResource(http)}

    return resources['datasets'].delete_dataset(dataset_id)


def create_dataset_item(
    dataset_id: str,
    name: str,
    input_data: Dict[str, Any],
    expected_output: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    flag_overrides: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new dataset item.

    Args:
        dataset_id: Dataset UUID to add item to
        name: Item name
        input_data: Input data dictionary
        expected_output: Expected output (optional)
        description: Item description (optional)
        tags: Item tags (optional)
        metadata: Additional metadata (optional)
        flag_overrides: Flag overrides (optional)
        api_key: API key for authentication
        agent_id: Agent ID

    Returns:
        Dictionary with datasetitem_id

    Raises:
        APIKeyVerificationError: If API key or agent ID is missing or invalid.
    """
    from ..init import get_resources, get_http
    from ...core.config import SDKConfig
    from ...api.client import HttpClient

    # Get or create resources
    resources = get_resources()
    if not resources or 'datasets' not in resources:
        load_dotenv()

        if api_key is None:
            api_key = os.getenv("LUCIDIC_API_KEY", None)
            if api_key is None:
                raise APIKeyVerificationError(
                    "Make sure to either pass your API key or set the LUCIDIC_API_KEY environment variable."
                )

        if agent_id is None:
            agent_id = os.getenv("LUCIDIC_AGENT_ID", None)

        config = SDKConfig.from_env(api_key=api_key, agent_id=agent_id)
        http = HttpClient(config)
        from ...api.resources.dataset import DatasetResource
        resources = {'datasets': DatasetResource(http)}

    return resources['datasets'].create_item(
        dataset_id, name, input_data,
        expected_output=expected_output,
        description=description,
        tags=tags,
        metadata=metadata,
        flag_overrides=flag_overrides
    )


def get_dataset_item(
    dataset_id: str,
    item_id: str,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get a specific dataset item.

    Args:
        dataset_id: Dataset UUID
        item_id: Item UUID
        api_key: API key for authentication
        agent_id: Agent ID

    Returns:
        Dataset item data

    Raises:
        APIKeyVerificationError: If API key or agent ID is missing or invalid.
    """
    from ..init import get_resources, get_http
    from ...core.config import SDKConfig
    from ...api.client import HttpClient

    # Get or create resources
    resources = get_resources()
    if not resources or 'datasets' not in resources:
        load_dotenv()

        if api_key is None:
            api_key = os.getenv("LUCIDIC_API_KEY", None)
            if api_key is None:
                raise APIKeyVerificationError(
                    "Make sure to either pass your API key or set the LUCIDIC_API_KEY environment variable."
                )

        if agent_id is None:
            agent_id = os.getenv("LUCIDIC_AGENT_ID", None)

        config = SDKConfig.from_env(api_key=api_key, agent_id=agent_id)
        http = HttpClient(config)
        from ...api.resources.dataset import DatasetResource
        resources = {'datasets': DatasetResource(http)}

    return resources['datasets'].get_item(dataset_id, item_id)


def update_dataset_item(
    dataset_id: str,
    item_id: str,
    name: Optional[str] = None,
    input_data: Optional[Dict[str, Any]] = None,
    expected_output: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    flag_overrides: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update a dataset item.

    Args:
        dataset_id: Dataset UUID
        item_id: Item UUID
        name: New name (optional)
        input_data: New input data (optional)
        expected_output: New expected output (optional)
        description: New description (optional)
        tags: New tags (optional)
        metadata: New metadata (optional)
        flag_overrides: New flag overrides (optional)
        api_key: API key for authentication
        agent_id: Agent ID

    Returns:
        Updated item data

    Raises:
        APIKeyVerificationError: If API key or agent ID is missing or invalid.
    """
    from ..init import get_resources, get_http
    from ...core.config import SDKConfig
    from ...api.client import HttpClient

    # Get or create resources
    resources = get_resources()
    if not resources or 'datasets' not in resources:
        load_dotenv()

        if api_key is None:
            api_key = os.getenv("LUCIDIC_API_KEY", None)
            if api_key is None:
                raise APIKeyVerificationError(
                    "Make sure to either pass your API key or set the LUCIDIC_API_KEY environment variable."
                )

        if agent_id is None:
            agent_id = os.getenv("LUCIDIC_AGENT_ID", None)

        config = SDKConfig.from_env(api_key=api_key, agent_id=agent_id)
        http = HttpClient(config)
        from ...api.resources.dataset import DatasetResource
        resources = {'datasets': DatasetResource(http)}

    kwargs = {}
    if name is not None:
        kwargs['name'] = name
    if input_data is not None:
        kwargs['input'] = input_data
    if expected_output is not None:
        kwargs['expected_output'] = expected_output
    if description is not None:
        kwargs['description'] = description
    if tags is not None:
        kwargs['tags'] = tags
    if metadata is not None:
        kwargs['metadata'] = metadata
    if flag_overrides is not None:
        kwargs['flag_overrides'] = flag_overrides

    return resources['datasets'].update_item(dataset_id, item_id, **kwargs)


def delete_dataset_item(
    dataset_id: str,
    item_id: str,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Delete a dataset item.

    Args:
        dataset_id: Dataset UUID
        item_id: Item UUID
        api_key: API key for authentication
        agent_id: Agent ID

    Returns:
        Success message

    Raises:
        APIKeyVerificationError: If API key or agent ID is missing or invalid.
    """
    from ..init import get_resources, get_http
    from ...core.config import SDKConfig
    from ...api.client import HttpClient

    # Get or create resources
    resources = get_resources()
    if not resources or 'datasets' not in resources:
        load_dotenv()

        if api_key is None:
            api_key = os.getenv("LUCIDIC_API_KEY", None)
            if api_key is None:
                raise APIKeyVerificationError(
                    "Make sure to either pass your API key or set the LUCIDIC_API_KEY environment variable."
                )

        if agent_id is None:
            agent_id = os.getenv("LUCIDIC_AGENT_ID", None)

        config = SDKConfig.from_env(api_key=api_key, agent_id=agent_id)
        http = HttpClient(config)
        from ...api.resources.dataset import DatasetResource
        resources = {'datasets': DatasetResource(http)}

    return resources['datasets'].delete_item(dataset_id, item_id)


def list_dataset_item_sessions(
    dataset_id: str,
    item_id: str,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List all sessions for a dataset item.

    Args:
        dataset_id: Dataset UUID
        item_id: Item UUID
        api_key: API key for authentication
        agent_id: Agent ID

    Returns:
        Dictionary with num_sessions and sessions list

    Raises:
        APIKeyVerificationError: If API key or agent ID is missing or invalid.
    """
    from ..init import get_resources, get_http
    from ...core.config import SDKConfig
    from ...api.client import HttpClient

    # Get or create resources
    resources = get_resources()
    if not resources or 'datasets' not in resources:
        load_dotenv()

        if api_key is None:
            api_key = os.getenv("LUCIDIC_API_KEY", None)
            if api_key is None:
                raise APIKeyVerificationError(
                    "Make sure to either pass your API key or set the LUCIDIC_API_KEY environment variable."
                )

        if agent_id is None:
            agent_id = os.getenv("LUCIDIC_AGENT_ID", None)

        config = SDKConfig.from_env(api_key=api_key, agent_id=agent_id)
        http = HttpClient(config)
        from ...api.resources.dataset import DatasetResource
        resources = {'datasets': DatasetResource(http)}

    return resources['datasets'].list_item_sessions(dataset_id, item_id)