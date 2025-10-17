"""
Client for the Pre.dev Architect API
"""

from typing import Optional, Dict, Any, Literal, List, Union
from dataclasses import dataclass
import requests
from .exceptions import PredevAPIError, AuthenticationError, RateLimitError


@dataclass
class AsyncResponse:
    """Async mode response class"""
    specId: str
    status: Literal['pending', 'processing', 'completed', 'failed']


@dataclass
class SpecResponse:
    """Status check response class"""
    _id: Optional[str] = None
    created: Optional[str] = None

    endpoint: Optional[Literal['fast_spec', 'deep_spec']] = None
    input: Optional[str] = None
    status: Optional[Literal['pending',
                             'processing', 'completed', 'failed']] = None
    success: Optional[bool] = None

    uploadedFileShortUrl: Optional[str] = None
    uploadedFileName: Optional[str] = None
    output: Optional[Any] = None
    outputFormat: Optional[Literal['markdown', 'url']] = None
    outputFileUrl: Optional[str] = None
    executionTime: Optional[int] = None

    predevUrl: Optional[str] = None
    lovableUrl: Optional[str] = None
    cursorUrl: Optional[str] = None
    v0Url: Optional[str] = None
    boltUrl: Optional[str] = None

    errorMessage: Optional[str] = None
    progress: Optional[str] = None


@dataclass
class ErrorResponse:
    """Error response class"""
    error: str
    message: str


@dataclass
class ListSpecsResponse:
    """List/Find specs response class"""
    specs: List['SpecResponse']
    total: int
    hasMore: bool


class PredevAPI:
    """
    Client for interacting with the Pre.dev Architect API.

    The API offers two main endpoints:
    - Fast Spec: Generate comprehensive specs quickly (ideal for MVPs and prototypes)
    - Deep Spec: Generate ultra-detailed specs for complex systems (enterprise-grade depth)

    Args:
        api_key: Your API key from pre.dev settings
        base_url: Base URL for the API (default: https://api.pre.dev)

    Example:
        >>> from predev_api import PredevAPI
        >>> client = PredevAPI(api_key="your_api_key")
        >>> result = client.fast_spec("Build a task management app")
        >>> print(result)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.pre.dev"
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

        # Set up headers with x-api-key
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }

    def fast_spec(
        self,
        input_text: str,
        output_format: Literal["url", "markdown"] = "url",
        current_context: Optional[str] = None,
        doc_urls: Optional[List[str]] = None
    ) -> SpecResponse:
        """
        Generate a fast specification for your project.

        Perfect for MVPs and prototypes with balanced depth and speed.

        Args:
            input_text: Description of the project or feature to generate specs for
            output_format: Format of the output - "url" or "markdown" (default: "url")
            current_context: Existing project/codebase context. When omitted, generates
                           full new project spec. When provided, generates feature addition spec.
            doc_urls: Array of documentation URLs to reference (e.g., API docs, design systems)

        Returns:
            API response as SpecResponse object

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
            PredevAPIError: For other API errors

        Example:
            >>> client = PredevAPI(api_key="your_key")
            >>> result = client.fast_spec(
            ...     input_text="Build a task management app with team collaboration",
            ...     output_format="url"
            ... )
        """
        return self._make_request(
            endpoint="/fast-spec",
            input_text=input_text,
            output_format=output_format,
            current_context=current_context,
            doc_urls=doc_urls
        )

    def deep_spec(
        self,
        input_text: str,
        output_format: Literal["url", "markdown"] = "url",
        current_context: Optional[str] = None,
        doc_urls: Optional[List[str]] = None
    ) -> SpecResponse:
        """
        Generate a deep specification for your project.

        Ultra-detailed specifications for complex systems with enterprise-grade depth
        and comprehensive analysis.

        Args:
            input_text: Description of the project or feature to generate specs for
            output_format: Format of the output - "url" or "markdown" (default: "url")
            current_context: Existing project/codebase context. When omitted, generates
                           full new project spec. When provided, generates feature addition spec.
            doc_urls: Array of documentation URLs to reference (e.g., API docs, design systems)

        Returns:
            API response as SpecResponse object

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
            PredevAPIError: For other API errors

        Example:
            >>> client = PredevAPI(api_key="your_key")
            >>> result = client.deep_spec(
            ...     input_text="Build an enterprise resource planning system",
            ...     output_format="url"
            ... )
        """
        return self._make_request(
            endpoint="/deep-spec",
            input_text=input_text,
            output_format=output_format,
            current_context=current_context,
            doc_urls=doc_urls
        )

    def fast_spec_async(
        self,
        input_text: str,
        output_format: Literal["url", "markdown"] = "url",
        current_context: Optional[str] = None,
        doc_urls: Optional[List[str]] = None
    ) -> AsyncResponse:
        """
        Generate a fast specification asynchronously for your project.

        Perfect for MVPs and prototypes with balanced depth and speed.
        Returns immediately with a request ID for polling the status.

        Args:
            input_text: Description of the project or feature to generate specs for
            output_format: Format of the output - "url" or "markdown" (default: "url")
            current_context: Existing project/codebase context. When omitted, generates
                           full new project spec. When provided, generates feature addition spec.
            doc_urls: Array of documentation URLs to reference (e.g., API docs, design systems)

        Returns:
            API response as AsyncResponse object with specId for polling

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
            PredevAPIError: For other API errors

        Example:
            >>> client = PredevAPI(api_key="your_key")
            >>> result = client.fast_spec_async(
            ...     input_text="Build a task management app with team collaboration",
            ...     output_format="url"
            ... )
            >>> # Poll for status using result.specId
            >>> status = client.get_spec_status(result.specId)
        """
        return self._make_request_async(
            endpoint="/fast-spec",
            input_text=input_text,
            output_format=output_format,
            current_context=current_context,
            doc_urls=doc_urls
        )

    def deep_spec_async(
        self,
        input_text: str,
        output_format: Literal["url", "markdown"] = "url",
        current_context: Optional[str] = None,
        doc_urls: Optional[List[str]] = None
    ) -> AsyncResponse:
        """
        Generate a deep specification asynchronously for your project.

        Ultra-detailed specifications for complex systems with enterprise-grade depth
        and comprehensive analysis. Returns immediately with a request ID for polling the status.

        Args:
            input_text: Description of the project or feature to generate specs for
            output_format: Format of the output - "url" or "markdown" (default: "url")
            current_context: Existing project/codebase context. When omitted, generates
                           full new project spec. When provided, generates feature addition spec.
            doc_urls: Array of documentation URLs to reference (e.g., API docs, design systems)

        Returns:
            API response as AsyncResponse object with specId for polling

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
            PredevAPIError: For other API errors

        Example:
            >>> client = PredevAPI(api_key="your_key")
            >>> result = client.deep_spec_async(
            ...     input_text="Build an enterprise resource planning system",
            ...     output_format="url"
            ... )
            >>> # Poll for status using result.specId
            >>> status = client.get_spec_status(result.specId)
        """
        return self._make_request_async(
            endpoint="/deep-spec",
            input_text=input_text,
            output_format=output_format,
            current_context=current_context,
            doc_urls=doc_urls
        )

    def get_spec_status(self, spec_id: str) -> SpecResponse:
        """
        Get the status of an async specification generation request.

        Args:
            spec_id: The ID of the specification request

        Returns:
            API response with status information

        Raises:
            AuthenticationError: If authentication fails
            PredevAPIError: For other API errors

        Example:
            >>> client = PredevAPI(api_key="your_key")
            >>> status = client.get_spec_status("spec_123")
        """
        url = f"{self.base_url}/spec-status/{spec_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=60)
            self._handle_response(response)
            return response.json()
        except requests.RequestException as e:
            raise PredevAPIError(f"Request failed: {str(e)}") from e

    def list_specs(
        self,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
        endpoint: Optional[Literal['fast_spec', 'deep_spec']] = None,
        status: Optional[Literal['pending',
                                 'processing', 'completed', 'failed']] = None
    ) -> ListSpecsResponse:
        """
        List all specs with optional filtering and pagination.

        Args:
            limit: Results per page (1-100, default: 20)
            skip: Offset for pagination (default: 0)
            endpoint: Filter by endpoint type
            status: Filter by status

        Returns:
            ListSpecsResponse with specs array and pagination metadata

        Raises:
            AuthenticationError: If authentication fails
            PredevAPIError: For other API errors

        Example:
            >>> client = PredevAPI(api_key="your_key")
            >>> # Get first 20 specs
            >>> result = client.list_specs()
            >>> # Get completed specs only
            >>> completed = client.list_specs(status='completed')
            >>> # Paginate: get specs 20-40
            >>> page2 = client.list_specs(skip=20, limit=20)
        """
        url = f"{self.base_url}/list-specs"
        params = {}

        if limit is not None:
            params['limit'] = limit
        if skip is not None:
            params['skip'] = skip
        if endpoint is not None:
            params['endpoint'] = endpoint
        if status is not None:
            params['status'] = status

        try:
            response = requests.get(
                url, headers=self.headers, params=params, timeout=60)
            self._handle_response(response)
            return response.json()
        except requests.RequestException as e:
            raise PredevAPIError(f"Request failed: {str(e)}") from e

    def find_specs(
        self,
        query: str,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
        endpoint: Optional[Literal['fast_spec', 'deep_spec']] = None,
        status: Optional[Literal['pending',
                                 'processing', 'completed', 'failed']] = None
    ) -> ListSpecsResponse:
        """
        Search for specs using regex patterns.

        Args:
            query: REQUIRED - Regex pattern (case-insensitive)
            limit: Results per page (1-100, default: 20)
            skip: Offset for pagination (default: 0)
            endpoint: Filter by endpoint type
            status: Filter by status

        Returns:
            ListSpecsResponse with matching specs and pagination metadata

        Raises:
            AuthenticationError: If authentication fails
            PredevAPIError: For other API errors

        Example:
            >>> client = PredevAPI(api_key="your_key")
            >>> # Search for "payment" specs
            >>> result = client.find_specs(query='payment')
            >>> # Search for specs starting with "Build"
            >>> builds = client.find_specs(query='^Build')
            >>> # Search: only completed specs mentioning "auth"
            >>> auth = client.find_specs(query='auth', status='completed')
        """
        url = f"{self.base_url}/find-specs"
        params = {'query': query}

        if limit is not None:
            params['limit'] = limit
        if skip is not None:
            params['skip'] = skip
        if endpoint is not None:
            params['endpoint'] = endpoint
        if status is not None:
            params['status'] = status

        try:
            response = requests.get(
                url, headers=self.headers, params=params, timeout=60)
            self._handle_response(response)
            return response.json()
        except requests.RequestException as e:
            raise PredevAPIError(f"Request failed: {str(e)}") from e

    def _make_request(
        self,
        endpoint: str,
        input_text: str,
        output_format: str,
        current_context: Optional[str] = None,
        doc_urls: Optional[List[str]] = None
    ) -> SpecResponse:
        """Make a POST request to the API."""
        url = f"{self.base_url}{endpoint}"
        payload = {
            "input": input_text,
            "outputFormat": output_format
        }

        if current_context is not None:
            payload["currentContext"] = current_context

        if doc_urls is not None:
            payload["docURLs"] = doc_urls

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=300  # 5 minutes for spec generation
            )
            self._handle_response(response)
            return response.json()
        except requests.RequestException as e:
            raise PredevAPIError(f"Request failed: {str(e)}") from e

    def _make_request_async(
        self,
        endpoint: str,
        input_text: str,
        output_format: str,
        current_context: Optional[str] = None,
        doc_urls: Optional[List[str]] = None
    ) -> AsyncResponse:
        """Make an async POST request to the API."""
        url = f"{self.base_url}{endpoint}"
        payload = {
            "input": input_text,
            "outputFormat": output_format,
            "async": True
        }

        if current_context is not None:
            payload["currentContext"] = current_context

        if doc_urls is not None:
            payload["docURLs"] = doc_urls

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=300  # 5 minutes for spec generation
            )
            self._handle_response(response)
            return response.json()
        except requests.RequestException as e:
            raise PredevAPIError(f"Request failed: {str(e)}") from e

    def _handle_response(self, response: requests.Response) -> None:
        """Handle API response and raise appropriate exceptions."""
        if response.status_code == 200:
            return

        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")

        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")

        try:
            error_data = response.json()
            error_message = error_data.get("error") or error_data.get(
                "message") or str(error_data)
        except Exception:
            error_message = response.text or "Unknown error"

        raise PredevAPIError(
            f"API request failed with status {response.status_code}: {error_message}"
        )
