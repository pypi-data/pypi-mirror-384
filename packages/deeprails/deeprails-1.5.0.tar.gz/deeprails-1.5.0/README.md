# Deeprails Python API library

<!-- prettier-ignore -->
[![PyPI version](https://img.shields.io/pypi/v/deeprails.svg?label=pypi%20(stable))](https://pypi.org/project/deeprails/)

The Deeprails Python library provides convenient access to the Deeprails REST API from any Python 3.8+
application. The library includes type definitions for all request params and response fields,
and offers both synchronous and asynchronous clients powered by [httpx](https://github.com/encode/httpx).

## Documentation

The REST API documentation can be found on [docs.deeprails.com](https://docs.deeprails.com). The full API of this library can be found in [api.md](api.md).

## Installation

```sh
# install from PyPI
pip install deeprails
```

## Usage

The full API of this library can be found in [api.md](api.md).

```python
import os
from deeprails import Deeprails

client = Deeprails(
    api_key=os.environ.get("DEEPRAILS_API_KEY"),  # This is the default and can be omitted
)

defend_response = client.defend.create_workflow(
    improvement_action="fixit",
    metrics={
        "completeness": 0.8,
        "instruction_adherence": 0.75,
    },
    name="Push Alert Workflow",
    type="custom",
)
print(defend_response.workflow_id)
```

While you can provide an `api_key` keyword argument,
we recommend using [python-dotenv](https://pypi.org/project/python-dotenv/)
to add `DEEPRAILS_API_KEY="My API Key"` to your `.env` file
so that your API Key is not stored in source control.

## Async usage

Simply import `AsyncDeeprails` instead of `Deeprails` and use `await` with each API call:

```python
import os
import asyncio
from deeprails import AsyncDeeprails

client = AsyncDeeprails(
    api_key=os.environ.get("DEEPRAILS_API_KEY"),  # This is the default and can be omitted
)


async def main() -> None:
    defend_response = await client.defend.create_workflow(
        improvement_action="fixit",
        metrics={
            "completeness": 0.8,
            "instruction_adherence": 0.75,
        },
        name="Push Alert Workflow",
        type="custom",
    )
    print(defend_response.workflow_id)


asyncio.run(main())
```

Functionality between the synchronous and asynchronous clients is otherwise identical.

### With aiohttp

By default, the async client uses `httpx` for HTTP requests. However, for improved concurrency performance you may also use `aiohttp` as the HTTP backend.

You can enable this by installing `aiohttp`:

```sh
# install from PyPI
pip install deeprails[aiohttp]
```

Then you can enable it by instantiating the client with `http_client=DefaultAioHttpClient()`:

```python
import asyncio
from deeprails import DefaultAioHttpClient
from deeprails import AsyncDeeprails


async def main() -> None:
    async with AsyncDeeprails(
        api_key="My API Key",
        http_client=DefaultAioHttpClient(),
    ) as client:
        defend_response = await client.defend.create_workflow(
            improvement_action="fixit",
            metrics={
                "completeness": 0.8,
                "instruction_adherence": 0.75,
            },
            name="Push Alert Workflow",
            type="custom",
        )
        print(defend_response.workflow_id)


asyncio.run(main())
```

## Using types

Nested request parameters are [TypedDicts](https://docs.python.org/3/library/typing.html#typing.TypedDict). Responses are [Pydantic models](https://docs.pydantic.dev) which also provide helper methods for things like:

- Serializing back into JSON, `model.to_json()`
- Converting to a dictionary, `model.to_dict()`

Typed requests and responses provide autocomplete and documentation within your editor. If you would like to see type errors in VS Code to help catch bugs earlier, set `python.analysis.typeCheckingMode` to `basic`.

## Nested params

Nested parameters are dictionaries, typed using `TypedDict`, for example:

```python
from deeprails import Deeprails

client = Deeprails()

workflow_event_response = client.defend.submit_event(
    workflow_id="workflow_id",
    model_input={"user_prompt": "user_prompt"},
    model_output="model_output",
    model_used="model_used",
    run_mode="precision_plus",
)
print(workflow_event_response.model_input)
```

## Handling errors

When the library is unable to connect to the API (for example, due to network connection problems or a timeout), a subclass of `deeprails.APIConnectionError` is raised.

When the API returns a non-success status code (that is, 4xx or 5xx
response), a subclass of `deeprails.APIStatusError` is raised, containing `status_code` and `response` properties.

All errors inherit from `deeprails.APIError`.

```python
import deeprails
from deeprails import Deeprails

client = Deeprails()

try:
    client.defend.create_workflow(
        improvement_action="fixit",
        metrics={
            "completeness": 0.8,
            "instruction_adherence": 0.75,
        },
        name="Push Alert Workflow",
        type="custom",
    )
except deeprails.APIConnectionError as e:
    print("The server could not be reached")
    print(e.__cause__)  # an underlying Exception, likely raised within httpx.
except deeprails.RateLimitError as e:
    print("A 429 status code was received; we should back off a bit.")
except deeprails.APIStatusError as e:
    print("Another non-200-range status code was received")
    print(e.status_code)
    print(e.response)
```

Error codes are as follows:

| Status Code | Error Type                 |
| ----------- | -------------------------- |
| 400         | `BadRequestError`          |
| 401         | `AuthenticationError`      |
| 403         | `PermissionDeniedError`    |
| 404         | `NotFoundError`            |
| 422         | `UnprocessableEntityError` |
| 429         | `RateLimitError`           |
| >=500       | `InternalServerError`      |
| N/A         | `APIConnectionError`       |

### Retries

Certain errors are automatically retried 2 times by default, with a short exponential backoff.
Connection errors (for example, due to a network connectivity problem), 408 Request Timeout, 409 Conflict,
429 Rate Limit, and >=500 Internal errors are all retried by default.

You can use the `max_retries` option to configure or disable retry settings:

```python
from deeprails import Deeprails

# Configure the default for all requests:
client = Deeprails(
    # default is 2
    max_retries=0,
)

# Or, configure per-request:
client.with_options(max_retries=5).defend.create_workflow(
    improvement_action="fixit",
    metrics={
        "completeness": 0.8,
        "instruction_adherence": 0.75,
    },
    name="Push Alert Workflow",
    type="custom",
)
```

### Timeouts

By default requests time out after 1 minute. You can configure this with a `timeout` option,
which accepts a float or an [`httpx.Timeout`](https://www.python-httpx.org/advanced/timeouts/#fine-tuning-the-configuration) object:

```python
from deeprails import Deeprails

# Configure the default for all requests:
client = Deeprails(
    # 20 seconds (default is 1 minute)
    timeout=20.0,
)

# More granular control:
client = Deeprails(
    timeout=httpx.Timeout(60.0, read=5.0, write=10.0, connect=2.0),
)

# Override per-request:
client.with_options(timeout=5.0).defend.create_workflow(
    improvement_action="fixit",
    metrics={
        "completeness": 0.8,
        "instruction_adherence": 0.75,
    },
    name="Push Alert Workflow",
    type="custom",
)
```

On timeout, an `APITimeoutError` is thrown.

Note that requests that time out are [retried twice by default](#retries).

## Advanced

### Logging

We use the standard library [`logging`](https://docs.python.org/3/library/logging.html) module.

You can enable logging by setting the environment variable `DEEPRAILS_LOG` to `info`.

```shell
$ export DEEPRAILS_LOG=info
```

Or to `debug` for more verbose logging.

### How to tell whether `None` means `null` or missing

In an API response, a field may be explicitly `null`, or missing entirely; in either case, its value is `None` in this library. You can differentiate the two cases with `.model_fields_set`:

```py
if response.my_field is None:
  if 'my_field' not in response.model_fields_set:
    print('Got json like {}, without a "my_field" key present at all.')
  else:
    print('Got json like {"my_field": null}.')
```

### Accessing raw response data (e.g. headers)

The "raw" Response object can be accessed by prefixing `.with_raw_response.` to any HTTP method call, e.g.,

```py
from deeprails import Deeprails

client = Deeprails()
response = client.defend.with_raw_response.create_workflow(
    improvement_action="fixit",
    metrics={
        "completeness": 0.8,
        "instruction_adherence": 0.75,
    },
    name="Push Alert Workflow",
    type="custom",
)
print(response.headers.get('X-My-Header'))

defend = response.parse()  # get the object that `defend.create_workflow()` would have returned
print(defend.workflow_id)
```

These methods return an [`APIResponse`](https://github.com/deeprails/deeprails-sdk-python/tree/main/src/deeprails/_response.py) object.

The async client returns an [`AsyncAPIResponse`](https://github.com/deeprails/deeprails-sdk-python/tree/main/src/deeprails/_response.py) with the same structure, the only difference being `await`able methods for reading the response content.

#### `.with_streaming_response`

The above interface eagerly reads the full response body when you make the request, which may not always be what you want.

To stream the response body, use `.with_streaming_response` instead, which requires a context manager and only reads the response body once you call `.read()`, `.text()`, `.json()`, `.iter_bytes()`, `.iter_text()`, `.iter_lines()` or `.parse()`. In the async client, these are async methods.

```python
with client.defend.with_streaming_response.create_workflow(
    improvement_action="fixit",
    metrics={
        "completeness": 0.8,
        "instruction_adherence": 0.75,
    },
    name="Push Alert Workflow",
    type="custom",
) as response:
    print(response.headers.get("X-My-Header"))

    for line in response.iter_lines():
        print(line)
```

The context manager is required so that the response will reliably be closed.

## Requirements

Python 3.8 or higher.
