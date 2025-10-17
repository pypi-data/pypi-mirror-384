# pre.dev Architect API - Python Client

A Python client library for the [Pre.dev Architect API](https://docs.pre.dev). Generate comprehensive software specifications using AI-powered analysis.

## Features

- 🚀 **Fast Spec**: Generate comprehensive specifications quickly - perfect for MVPs and prototypes
- 🔍 **Deep Spec**: Generate ultra-detailed specifications for complex systems with enterprise-grade depth
- ⚡ **Async Spec**: Non-blocking async methods for long-running requests
- 📊 **Status Tracking**: Check the status of async specification generation requests
- ✨ **Type Hints**: Full type annotations for better IDE support
- 🛡️ **Error Handling**: Custom exceptions for different error scenarios

## Installation

```bash
pip install predev-api
```

## Quick Start

```python
from predev_api import PredevAPI

# Initialize the predev client with your API key
predev = PredevAPI(api_key="your_api_key_here")

# Generate a fast specification
result = predev.fast_spec(
    input_text="Build a task management app with team collaboration",
    output_format="url"
)

print(result)
```

## Authentication

The Pre.dev API uses API key authentication. Get your API key from the [pre.dev dashboard](https://pre.dev) under Settings → API Keys:

```python
predev = PredevAPI(api_key="your_api_key")
```

## API Methods

### Synchronous Methods

#### `fast_spec(input_text: str, output_format: Literal["url", "markdown"] = "url", current_context: Optional[str] = None, doc_urls: Optional[List[str]] = None) -> SpecResponse`

Generate a fast specification (30-40 seconds, 10 credits).

**Parameters:**
- `input_text` **(required)**: `str` - Description of what you want to build
- `output_format` **(optional)**: `"url" | "markdown"` - Output format (default: `"url"`)
- `current_context` **(optional)**: `str` - Existing project context
- `doc_urls` **(optional)**: `List[str]` - Documentation URLs to reference

**Returns:** `SpecResponse` object with complete specification data

**Example:**
```python
result = predev.fast_spec(
    input_text="Build a SaaS project management tool with real-time collaboration",
    output_format="url"
)
```

#### `deep_spec(input_text: str, output_format: Literal["url", "markdown"] = "url", current_context: Optional[str] = None, doc_urls: Optional[List[str]] = None) -> SpecResponse`

Generate a deep specification (2-3 minutes, 50 credits).

**Parameters:** Same as `fast_spec`

**Returns:** `SpecResponse` object with comprehensive specification data

**Example:**
```python
result = predev.deep_spec(
    input_text="Build a healthcare platform with HIPAA compliance",
    output_format="url"
)
```

### Asynchronous Methods

#### `fast_spec_async(input_text: str, output_format: Literal["url", "markdown"] = "url", current_context: Optional[str] = None, doc_urls: Optional[List[str]] = None) -> AsyncResponse`

Generate a fast specification asynchronously (returns immediately).

**Parameters:** Same as `fast_spec`

**Returns:** `AsyncResponse` object with `specId` for polling

**Example:**
```python
result = predev.fast_spec_async(
    input_text="Build a comprehensive e-commerce platform",
    output_format="url"
)
# Returns: AsyncResponse(specId="spec_123", status="pending")
```

#### `deep_spec_async(input_text: str, output_format: Literal["url", "markdown"] = "url", current_context: Optional[str] = None, doc_urls: Optional[List[str]] = None) -> AsyncResponse`

Generate a deep specification asynchronously (returns immediately).

**Parameters:** Same as `fast_spec`

**Returns:** `AsyncResponse` object with `specId` for polling

**Example:**
```python
result = predev.deep_spec_async(
    input_text="Build a fintech platform with regulatory compliance",
    output_format="url"
)
# Returns: AsyncResponse(specId="spec_456", status="pending")
```

### Status Checking

#### `get_spec_status(spec_id: str) -> SpecResponse`

Check the status of an async specification generation request.

**Parameters:**
- `spec_id` **(required)**: `str` - The specification ID from async methods

**Returns:** `SpecResponse` object with current status and data (when completed)

**Example:**
```python
status = predev.get_spec_status("spec_123")
# Returns SpecResponse with status: "pending" | "processing" | "completed" | "failed"
```

### Listing and Searching Specs

#### `list_specs(limit: Optional[int] = None, skip: Optional[int] = None, endpoint: Optional[Literal["fast_spec", "deep_spec"]] = None, status: Optional[Literal["pending", "processing", "completed", "failed"]] = None) -> ListSpecsResponse`

List all specs with optional filtering and pagination.

**Parameters:**
- `limit` **(optional)**: `int` - Results per page (1-100, default: 20)
- `skip` **(optional)**: `int` - Offset for pagination (default: 0)
- `endpoint` **(optional)**: `"fast_spec" | "deep_spec"` - Filter by endpoint type
- `status` **(optional)**: `"pending" | "processing" | "completed" | "failed"` - Filter by status

**Returns:** `ListSpecsResponse` object with specs array and pagination metadata

**Examples:**
```python
# Get first 20 specs
result = predev.list_specs()

# Get completed specs only
completed = predev.list_specs(status='completed')

# Paginate: get specs 20-40
page2 = predev.list_specs(skip=20, limit=20)

# Filter by endpoint type
fast_specs = predev.list_specs(endpoint='fast_spec')
```

#### `find_specs(query: str, limit: Optional[int] = None, skip: Optional[int] = None, endpoint: Optional[Literal["fast_spec", "deep_spec"]] = None, status: Optional[Literal["pending", "processing", "completed", "failed"]] = None) -> ListSpecsResponse`

Search for specs using regex patterns.

**Parameters:**
- `query` **(required)**: `str` - Regex pattern (case-insensitive)
- `limit` **(optional)**: `int` - Results per page (1-100, default: 20)
- `skip` **(optional)**: `int` - Offset for pagination (default: 0)
- `endpoint` **(optional)**: `"fast_spec" | "deep_spec"` - Filter by endpoint type
- `status` **(optional)**: `"pending" | "processing" | "completed" | "failed"` - Filter by status

**Returns:** `ListSpecsResponse` object with matching specs and pagination metadata

**Examples:**
```python
# Search for "payment" specs
payment_specs = predev.find_specs(query='payment')

# Search for specs starting with "Build"
build_specs = predev.find_specs(query='^Build')

# Search: only completed specs mentioning "auth"
auth_specs = predev.find_specs(
    query='auth',
    status='completed'
)

# Complex regex: find SaaS or SASS projects
saas_specs = predev.find_specs(query='saas|sass')
```

**Regex Pattern Examples:**

| Pattern | Matches |
|---------|---------|
| `payment` | "payment", "Payment", "make payment" |
| `^Build` | Specs starting with "Build" |
| `platform$` | Specs ending with "platform" |
| `(API\|REST)` | Either "API" or "REST" |
| `auth.*system` | "auth" then anything then "system" |
| `\\d{3,}` | 3+ digits (budgets, quantities) |
| `saas\|sass` | SaaS or SASS |

## Response Types

### `AsyncResponse`
```python
@dataclass
class AsyncResponse:
    specId: str                                    # Unique ID for polling (e.g., "spec_abc123")
    status: Literal['pending', 'processing', 'completed', 'failed']
```

### `SpecResponse`
```python
@dataclass
class SpecResponse:
    # Basic info
    _id: Optional[str] = None                      # Internal ID
    created: Optional[str] = None                  # ISO timestamp
    endpoint: Optional[Literal['fast_spec', 'deep_spec']] = None
    input: Optional[str] = None                    # Original input text
    status: Optional[Literal['pending', 'processing', 'completed', 'failed']] = None
    success: Optional[bool] = None

    # Output data (when completed)
    uploadedFileShortUrl: Optional[str] = None    # URL to input file
    uploadedFileName: Optional[str] = None        # Name of input file
    output: Optional[Any] = None                  # Raw content or URL
    outputFormat: Optional[Literal['markdown', 'url']] = None
    outputFileUrl: Optional[str] = None           # Full URL to hosted spec
    executionTime: Optional[int] = None           # Processing time in milliseconds

    # Integration URLs (when completed)
    predevUrl: Optional[str] = None               # Link to pre.dev project
    lovableUrl: Optional[str] = None              # Link to generate with Lovable
    cursorUrl: Optional[str] = None               # Link to generate with Cursor
    v0Url: Optional[str] = None                   # Link to generate with v0
    boltUrl: Optional[str] = None                 # Link to generate with Bolt

    # Error handling
    errorMessage: Optional[str] = None            # Error details if failed
    progress: Optional[str] = None                # Progress information
```

### `ListSpecsResponse`
```python
@dataclass
class ListSpecsResponse:
    specs: List[SpecResponse]  # Array of spec objects
    total: int                 # Total count of matching specs
    hasMore: bool              # Whether more results are available
```

## Examples Directory

Check out the [examples directory](https://github.com/predotdev/predev-api/tree/main/predev-api-python/examples) for detailed usage examples.

## Documentation

For more information about the Pre.dev Architect API, visit:
- [API Documentation](https://docs.pre.dev)
- [pre.dev Website](https://pre.dev)

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/predotdev/predev-api).
