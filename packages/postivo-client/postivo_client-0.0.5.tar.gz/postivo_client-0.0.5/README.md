[![PyPI - Version](https://img.shields.io/pypi/v/postivo-client)](https://pypi.org/project/postivo-client/)
[![GitHub License](https://img.shields.io/github/license/postivo/python-client)](https://github.com/postivo/python-client/blob/main/LICENSE)
[![Static Badge](https://img.shields.io/badge/built_by-Speakeasy-yellow)](https://www.speakeasy.com/?utm_source=postivo-client&utm_campaign=python)
# POSTIVO.PL REST API Client SDK for Python (postivo-client)

This package provides the **POSTIVO.PL Hybrid Mail Services SDK** for Python, allowing you to dispatch shipments directly from your application via the [POSTIVO.PL](https://postivo.pl) platform.

## Additional documentation:

Comprehensive documentation of all methods and types is available below in [Available Resources and Operations](#available-resources-and-operations).

You can also refer to the [REST API v1 documentation](https://api.postivo.pl/rest/v1/) for additional details about this SDK.

<!-- No Summary [summary] -->

<!-- Start Table of Contents [toc] -->
## Table of Contents
<!-- $toc-max-depth=2 -->
* [POSTIVO.PL REST API Client SDK for Python (postivo-client)](#postivopl-rest-api-client-sdk-for-python-postivo-client)
  * [Additional documentation:](#additional-documentation)
  * [SDK Installation](#sdk-installation)
  * [IDE Support](#ide-support)
  * [SDK Example Usage](#sdk-example-usage)
  * [Authentication](#authentication)
  * [Available Resources and Operations](#available-resources-and-operations)
  * [Retries](#retries)
  * [Error Handling](#error-handling)
  * [Server Selection](#server-selection)
  * [Custom HTTP Client](#custom-http-client)
  * [Resource Management](#resource-management)
  * [Debugging](#debugging)
* [Development](#development)
  * [Maturity](#maturity)
  * [Contributions](#contributions)

<!-- End Table of Contents [toc] -->

<!-- Start SDK Installation [installation] -->
## SDK Installation

> [!NOTE]
> **Python version upgrade policy**
>
> Once a Python version reaches its [official end of life date](https://devguide.python.org/versions/), a 3-month grace period is provided for users to upgrade. Following this grace period, the minimum python version supported in the SDK will be updated.

The SDK can be installed with *uv*, *pip*, or *poetry* package managers.

### uv

*uv* is a fast Python package installer and resolver, designed as a drop-in replacement for pip and pip-tools. It's recommended for its speed and modern Python tooling capabilities.

```bash
uv add postivo-client
```

### PIP

*PIP* is the default package installer for Python, enabling easy installation and management of packages from PyPI via the command line.

```bash
pip install postivo-client
```

### Poetry

*Poetry* is a modern tool that simplifies dependency management and package publishing by using a single `pyproject.toml` file to handle project metadata and dependencies.

```bash
poetry add postivo-client
```

### Shell and script usage with `uv`

You can use this SDK in a Python shell with [uv](https://docs.astral.sh/uv/) and the `uvx` command that comes with it like so:

```shell
uvx --from postivo-client python
```

It's also possible to write a standalone Python script without needing to set up a whole project like so:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "postivo-client",
# ]
# ///

from postivo_client import Client

sdk = Client(
  # SDK arguments
)

# Rest of script here...
```

Once that is saved to a file, you can run it with `uv run script.py` where
`script.py` can be replaced with the actual file name.
<!-- End SDK Installation [installation] -->

<!-- Start IDE Support [idesupport] -->
## IDE Support

### PyCharm

Generally, the SDK will work well with most IDEs out of the box. However, when using PyCharm, you can enjoy much better integration with Pydantic by installing an additional plugin.

- [PyCharm Pydantic Plugin](https://docs.pydantic.dev/latest/integrations/pycharm/)
<!-- End IDE Support [idesupport] -->

<!-- Start SDK Example Usage [usage] -->
## SDK Example Usage

### Sending Shipment to single recipient

This example demonstrates simple sending Shipment to a single recipient:

```python
# Synchronous Example
from postivo_client import Client


with Client(
    bearer="<YOUR API ACCESS TOKEN>",
) as client:

    res = client.shipments.dispatch(recipients={
        "name": "Jan Nowak",
        "name2": "Firma testowa Sp. z o.o.",
        "address": "ul. Testowa",
        "home_number": "23",
        "flat_number": "2",
        "post_code": "00-999",
        "city": "Warszawa",
        "country": "PL",
        "phone_number": "+48666666666",
        "postscript": "Komunikat",
        "custom_id": "1234567890",
    }, documents=[
        {
            "file_stream": "<document_1 content encoded to base64>",
            "file_name": "document1.pdf",
        },
        {
            "file_stream": "<document_2 content encoded to base64>",
            "file_name": "document2.pdf",
        },
    ], options={
        "predefined_config_id": 2670,
    })

    # Handle response
    print(res)
```

</br>

The same SDK client can also be used to make asynchronous requests by importing asyncio.

```python
# Asynchronous Example
import asyncio
from postivo_client import Client

async def main():

    async with Client(
        bearer="<YOUR API ACCESS TOKEN>",
    ) as client:

        res = await client.shipments.dispatch_async(recipients={
            "name": "Jan Nowak",
            "name2": "Firma testowa Sp. z o.o.",
            "address": "ul. Testowa",
            "home_number": "23",
            "flat_number": "2",
            "post_code": "00-999",
            "city": "Warszawa",
            "country": "PL",
            "phone_number": "+48666666666",
            "postscript": "Komunikat",
            "custom_id": "1234567890",
        }, documents=[
            {
                "file_stream": "<document_1 content encoded to base64>",
                "file_name": "document1.pdf",
            },
            {
                "file_stream": "<document_2 content encoded to base64>",
                "file_name": "document2.pdf",
            },
        ], options={
            "predefined_config_id": 2670,
        })

        # Handle response
        print(res)

asyncio.run(main())
```

### Checking the price of a shipment for single recipient

This example demonstrates simple checking the price of a Shipment to a single recipient:

```python
# Synchronous Example
from postivo_client import Client


with Client(
    bearer="<YOUR API ACCESS TOKEN>",
) as client:

    res = client.shipments.price(recipients={
        "name": "Jan Nowak",
        "name2": "Firma testowa Sp. z o.o.",
        "address": "ul. Testowa",
        "home_number": "23",
        "flat_number": "2",
        "post_code": "00-999",
        "city": "Warszawa",
        "country": "PL",
        "phone_number": "+48666666666",
        "postscript": "Komunikat",
        "custom_id": "1234567890",
    }, documents=[
        {
            "file_stream": "<document_1 content encoded to base64>",
            "file_name": "document1.pdf",
        },
        {
            "file_stream": "<document_2 content encoded to base64>",
            "file_name": "document2.pdf",
        },
    ], options={
        "predefined_config_id": 2670,
    })

    # Handle response
    print(res)
```

</br>

The same SDK client can also be used to make asynchronous requests by importing asyncio.

```python
# Asynchronous Example
import asyncio
from postivo_client import Client

async def main():

    async with Client(
        bearer="<YOUR API ACCESS TOKEN>",
    ) as client:

        res = await client.shipments.price_async(recipients={
            "name": "Jan Nowak",
            "name2": "Firma testowa Sp. z o.o.",
            "address": "ul. Testowa",
            "home_number": "23",
            "flat_number": "2",
            "post_code": "00-999",
            "city": "Warszawa",
            "country": "PL",
            "phone_number": "+48666666666",
            "postscript": "Komunikat",
            "custom_id": "1234567890",
        }, documents=[
            {
                "file_stream": "<document_1 content encoded to base64>",
                "file_name": "document1.pdf",
            },
            {
                "file_stream": "<document_2 content encoded to base64>",
                "file_name": "document2.pdf",
            },
        ], options={
            "predefined_config_id": 2670,
        })

        # Handle response
        print(res)

asyncio.run(main())
```
<!-- End SDK Example Usage [usage] -->

<!-- Start Authentication [security] -->
## Authentication

### Per-Client Security Schemes

This SDK supports the following security scheme globally:

| Name     | Type | Scheme      | Environment Variable |
| -------- | ---- | ----------- | -------------------- |
| `bearer` | http | HTTP Bearer | `CLIENT_BEARER`      |

To authenticate with the API the `bearer` parameter must be set when initializing the SDK client instance. For example:
```python
from postivo_client import Client


with Client(
    bearer="<YOUR API ACCESS TOKEN>",
) as client:

    res = client.accounts.get()

    # Handle response
    print(res)

```
<!-- End Authentication [security] -->

<!-- Start Available Resources and Operations [operations] -->
## Available Resources and Operations

<details open>
<summary>Available methods</summary>

### [accounts](docs/sdks/accounts/README.md)

* [get](docs/sdks/accounts/README.md#get) - Retrieve account details
* [get_subaccount](docs/sdks/accounts/README.md#get_subaccount) - Get subaccount details

#### [address_book.contacts](docs/sdks/contacts/README.md)

* [list](docs/sdks/contacts/README.md#list) - List contacts
* [add](docs/sdks/contacts/README.md#add) - Add a new contact
* [get](docs/sdks/contacts/README.md#get) - Retrieve contact details
* [update](docs/sdks/contacts/README.md#update) - Update a contact
* [delete](docs/sdks/contacts/README.md#delete) - Delete a contact
* [remove_from_group](docs/sdks/contacts/README.md#remove_from_group) - Remove a contact from a group
* [add_to_group](docs/sdks/contacts/README.md#add_to_group) - Add a contact to a group

#### [address_book.contacts.by_ext_id](docs/sdks/byextid/README.md)

* [get](docs/sdks/byextid/README.md#get) - Retrieve contact details by EXT_ID
* [update](docs/sdks/byextid/README.md#update) - Update a contact by EXT_ID
* [delete](docs/sdks/byextid/README.md#delete) - Delete a contact by EXT_ID
* [remove_from_group](docs/sdks/byextid/README.md#remove_from_group) - Remove a contact from a group by EXT_ID
* [add_to_group](docs/sdks/byextid/README.md#add_to_group) - Add a contact to a group by EXT_ID

#### [address_book.groups](docs/sdks/groups/README.md)

* [list](docs/sdks/groups/README.md#list) - List groups
* [add](docs/sdks/groups/README.md#add) - Add a new group
* [get](docs/sdks/groups/README.md#get) - Retrieve group details
* [update](docs/sdks/groups/README.md#update) - Update a group
* [delete](docs/sdks/groups/README.md#delete) - Delete a group

### [common](docs/sdks/common/README.md)

* [ping](docs/sdks/common/README.md#ping) - Check API availability and version

### [metadata](docs/sdks/metadata/README.md)

* [list](docs/sdks/metadata/README.md#list) - List metadata
* [get_predefined_configs](docs/sdks/metadata/README.md#get_predefined_configs) - List predefined configs

### [senders](docs/sdks/senders/README.md)

* [list](docs/sdks/senders/README.md#list) - List senders
* [add](docs/sdks/senders/README.md#add) - Add a new sender
* [delete](docs/sdks/senders/README.md#delete) - Delete a sender
* [verify](docs/sdks/senders/README.md#verify) - Verify sender

### [shipments](docs/sdks/shipments/README.md)

* [status](docs/sdks/shipments/README.md#status) - Retrieve shipment details with status events
* [cancel](docs/sdks/shipments/README.md#cancel) - Cancel shipments
* [dispatch](docs/sdks/shipments/README.md#dispatch) - Dispatch a new shipment
* [documents](docs/sdks/shipments/README.md#documents) - Retrieve documents related to a shipment
* [price](docs/sdks/shipments/README.md#price) - Check the shipment price

</details>
<!-- End Available Resources and Operations [operations] -->

<!-- Start Retries [retries] -->
## Retries

Some of the endpoints in this SDK support retries. If you use the SDK without any configuration, it will fall back to the default retry strategy provided by the API. However, the default retry strategy can be overridden on a per-operation basis, or across the entire SDK.

To change the default retry strategy for a single API call, simply provide a `RetryConfig` object to the call:
```python
from postivo_client import Client
from postivo_client.utils import BackoffStrategy, RetryConfig


with Client(
    bearer="<YOUR API ACCESS TOKEN>",
) as client:

    res = client.accounts.get(,
        RetryConfig("backoff", BackoffStrategy(1, 50, 1.1, 100), False))

    # Handle response
    print(res)

```

If you'd like to override the default retry strategy for all operations that support retries, you can use the `retry_config` optional parameter when initializing the SDK:
```python
from postivo_client import Client
from postivo_client.utils import BackoffStrategy, RetryConfig


with Client(
    retry_config=RetryConfig("backoff", BackoffStrategy(1, 50, 1.1, 100), False),
    bearer="<YOUR API ACCESS TOKEN>",
) as client:

    res = client.accounts.get()

    # Handle response
    print(res)

```
<!-- End Retries [retries] -->

<!-- Start Error Handling [errors] -->
## Error Handling

[`ClientError`](./src/postivo_client/errors/clienterror.py) is the base class for all HTTP error responses. It has the following properties:

| Property           | Type             | Description                                                                             |
| ------------------ | ---------------- | --------------------------------------------------------------------------------------- |
| `err.message`      | `str`            | Error message                                                                           |
| `err.status_code`  | `int`            | HTTP response status code eg `404`                                                      |
| `err.headers`      | `httpx.Headers`  | HTTP response headers                                                                   |
| `err.body`         | `str`            | HTTP body. Can be empty string if no body is returned.                                  |
| `err.raw_response` | `httpx.Response` | Raw HTTP response                                                                       |
| `err.data`         |                  | Optional. Some errors may contain structured data. [See Error Classes](#error-classes). |

### Example
```python
from postivo_client import Client, errors


with Client(
    bearer="<YOUR API ACCESS TOKEN>",
) as client:
    res = None
    try:

        res = client.accounts.get()

        # Handle response
        print(res)


    except errors.ClientError as e:
        # The base class for HTTP error responses
        print(e.message)
        print(e.status_code)
        print(e.body)
        print(e.headers)
        print(e.raw_response)

        # Depending on the method different errors may be thrown
        if isinstance(e, errors.ErrorResponse):
            print(e.data.type)  # Optional[str]
            print(e.data.status)  # Optional[int]
            print(e.data.title)  # Optional[str]
            print(e.data.detail)  # Optional[str]
            print(e.data.code)  # Optional[str]
```

### Error Classes
**Primary errors:**
* [`ClientError`](./src/postivo_client/errors/clienterror.py): The base class for HTTP error responses.
  * [`ErrorResponse`](./src/postivo_client/errors/errorresponse.py): Problem Details object (RFC 9457) describing the error.

<details><summary>Less common errors (5)</summary>

<br />

**Network errors:**
* [`httpx.RequestError`](https://www.python-httpx.org/exceptions/#httpx.RequestError): Base class for request errors.
    * [`httpx.ConnectError`](https://www.python-httpx.org/exceptions/#httpx.ConnectError): HTTP client was unable to make a request to a server.
    * [`httpx.TimeoutException`](https://www.python-httpx.org/exceptions/#httpx.TimeoutException): HTTP request timed out.


**Inherit from [`ClientError`](./src/postivo_client/errors/clienterror.py)**:
* [`ResponseValidationError`](./src/postivo_client/errors/responsevalidationerror.py): Type mismatch between the response data and the expected Pydantic model. Provides access to the Pydantic validation error via the `cause` attribute.

</details>
<!-- End Error Handling [errors] -->

<!-- Start Server Selection [server] -->
## Server Selection

### Select Server by Name

You can override the default server globally by passing a server name to the `server: str` optional parameter when initializing the SDK client instance. The selected server will then be used as the default on the operations that use it. This table lists the names associated with the available servers:

| Name      | Server                                   | Description           |
| --------- | ---------------------------------------- | --------------------- |
| `prod`    | `https://api.postivo.pl/rest/v1`         | Production system     |
| `sandbox` | `https://api.postivo.pl/rest-sandbox/v1` | Test system (SANDBOX) |

#### Example

```python
from postivo_client import Client


with Client(
    server="sandbox",
    bearer="<YOUR API ACCESS TOKEN>",
) as client:

    res = client.accounts.get()

    # Handle response
    print(res)

```

### Override Server URL Per-Client

The default server can also be overridden globally by passing a URL to the `server_url: str` optional parameter when initializing the SDK client instance. For example:
```python
from postivo_client import Client


with Client(
    server_url="https://api.postivo.pl/rest/v1",
    bearer="<YOUR API ACCESS TOKEN>",
) as client:

    res = client.accounts.get()

    # Handle response
    print(res)

```
<!-- End Server Selection [server] -->

<!-- Start Custom HTTP Client [http-client] -->
## Custom HTTP Client

The Python SDK makes API calls using the [httpx](https://www.python-httpx.org/) HTTP library.  In order to provide a convenient way to configure timeouts, cookies, proxies, custom headers, and other low-level configuration, you can initialize the SDK client with your own HTTP client instance.
Depending on whether you are using the sync or async version of the SDK, you can pass an instance of `HttpClient` or `AsyncHttpClient` respectively, which are Protocol's ensuring that the client has the necessary methods to make API calls.
This allows you to wrap the client with your own custom logic, such as adding custom headers, logging, or error handling, or you can just pass an instance of `httpx.Client` or `httpx.AsyncClient` directly.

For example, you could specify a header for every request that this sdk makes as follows:
```python
from postivo_client import Client
import httpx

http_client = httpx.Client(headers={"x-custom-header": "someValue"})
s = Client(client=http_client)
```

or you could wrap the client with your own custom logic:
```python
from postivo_client import Client
from postivo_client.httpclient import AsyncHttpClient
import httpx

class CustomClient(AsyncHttpClient):
    client: AsyncHttpClient

    def __init__(self, client: AsyncHttpClient):
        self.client = client

    async def send(
        self,
        request: httpx.Request,
        *,
        stream: bool = False,
        auth: Union[
            httpx._types.AuthTypes, httpx._client.UseClientDefault, None
        ] = httpx.USE_CLIENT_DEFAULT,
        follow_redirects: Union[
            bool, httpx._client.UseClientDefault
        ] = httpx.USE_CLIENT_DEFAULT,
    ) -> httpx.Response:
        request.headers["Client-Level-Header"] = "added by client"

        return await self.client.send(
            request, stream=stream, auth=auth, follow_redirects=follow_redirects
        )

    def build_request(
        self,
        method: str,
        url: httpx._types.URLTypes,
        *,
        content: Optional[httpx._types.RequestContent] = None,
        data: Optional[httpx._types.RequestData] = None,
        files: Optional[httpx._types.RequestFiles] = None,
        json: Optional[Any] = None,
        params: Optional[httpx._types.QueryParamTypes] = None,
        headers: Optional[httpx._types.HeaderTypes] = None,
        cookies: Optional[httpx._types.CookieTypes] = None,
        timeout: Union[
            httpx._types.TimeoutTypes, httpx._client.UseClientDefault
        ] = httpx.USE_CLIENT_DEFAULT,
        extensions: Optional[httpx._types.RequestExtensions] = None,
    ) -> httpx.Request:
        return self.client.build_request(
            method,
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            extensions=extensions,
        )

s = Client(async_client=CustomClient(httpx.AsyncClient()))
```
<!-- End Custom HTTP Client [http-client] -->

<!-- Start Resource Management [resource-management] -->
## Resource Management

The `Client` class implements the context manager protocol and registers a finalizer function to close the underlying sync and async HTTPX clients it uses under the hood. This will close HTTP connections, release memory and free up other resources held by the SDK. In short-lived Python programs and notebooks that make a few SDK method calls, resource management may not be a concern. However, in longer-lived programs, it is beneficial to create a single SDK instance via a [context manager][context-manager] and reuse it across the application.

[context-manager]: https://docs.python.org/3/reference/datamodel.html#context-managers

```python
from postivo_client import Client
def main():

    with Client(
        bearer="<YOUR API ACCESS TOKEN>",
    ) as client:
        # Rest of application here...


# Or when using async:
async def amain():

    async with Client(
        bearer="<YOUR API ACCESS TOKEN>",
    ) as client:
        # Rest of application here...
```
<!-- End Resource Management [resource-management] -->

<!-- Start Debugging [debug] -->
## Debugging

You can setup your SDK to emit debug logs for SDK requests and responses.

You can pass your own logger class directly into your SDK.
```python
from postivo_client import Client
import logging

logging.basicConfig(level=logging.DEBUG)
s = Client(debug_logger=logging.getLogger("postivo_client"))
```

You can also enable a default debug logger by setting an environment variable `CLIENT_DEBUG` to true.
<!-- End Debugging [debug] -->

<!-- Placeholder for Future Speakeasy SDK Sections -->

# Development

## Maturity

This SDK is in beta, and there may be breaking changes between versions without a major version update. Therefore, we recommend pinning usage
to a specific package version. This way, you can install the same version each time without breaking changes unless you are intentionally
looking for the latest version.

## Contributions

While we value open-source contributions to this SDK, this library is generated programmatically. Any manual changes added to internal files will be overwritten on the next generation. 
We look forward to hearing your feedback. Feel free to open a PR or an issue with a proof of concept and we'll do our best to include it in a future release.