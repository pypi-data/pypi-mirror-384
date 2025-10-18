
# abstract_apis 0.0.0.81

## Description
The `abstract_apis` module is a Python utility designed to facilitate HTTP requests in Python applications, with a focus on handling JSON data, interacting with custom API endpoints, and parsing complex nested JSON responses. Particularly, the module provides utilities for HTTP request management essential tasks such as header management, URL construction, and response parsing. It offers both synchronous and asynchronous request capabilities and has extended support for the Solana blockchain APIs via remote procedure call (RPC) requests. Some scripts also provide an interactive GUI for testing API functions and manipulate API response data.

## Features and Scripts Overview
- HTTP Request Management: Provides utilities for sending GET and POST requests and handles the respective responses. Refer to `make_request.py` and `async_make_request.py` scripts.
- URL and Endpoint Management: Offers functions to manage URL and endpoints. Refer to `abstract_api_calls.py` and `request_utils.py` scripts.
- Solana Blockchain API Manipulation: Extensions and utilities for handling RPC calls to Solana Blockchain. Refer to `body_get.py`, `solana_rpc_client.py`, and `variables.py` scripts.
- Response Data Retrieval: Includes methods for querying response data from a database. Refer to `dbQuery.py`.
- Interactive GUI: The module includes a script with an interactive GUI for testing API functions. Refer to `get_api_window.py` script.
- General Utilities: Several utility functions are present for tasks like string and JSON handling. Refer to the `request_utils.py` script.


### internal Scripts Overview


-`abstract_api_calls`
src/abstract_apis/abstract_api_calls.py
The provided script mainly focuses on handling URL management and HTTP post requests for various predefined websites. It starts by defining URLs for three different sites in the `get_urls` function and then defines multimedia API links for these websites in the `get_api_links` function. The `get_url` method is used to verify and return the appropriate URL for a given domain. The `get_api_link` function is used to concatenate the domain and the endpoint, but also ensures the URL doesn't have repeating sections. `make_request_link` uses the above helper methods to construct a complete URL and make a post HTTP request using the `postRequest` function from the imported `make_request.py` script. The `abstract_api_call` function is the high-level function that uses `make_request_link` to return the HTTP response of specific API endpoints from the given websites.



-`async_make_request`
src/abstract_apis/async_make_request.py
The async_make_request.py script of the abstract_apis module provides a set of methods for handling asynchronous HTTP requests. It relies heavily on the asyncio and aiohttp Python libraries to manage event loops, create client sessions, and send HTTP requests.

The script starts with several utility functions to manage async behavior. The `run_async` function manages the asyncio event loop to run asyncio coroutines. `get_async_response` runs an asynchronous function and returns the result using `run_async`.

The `getAsyncRequest`, `postAsyncRequest`, `asyncMakeRequest`, `asyncPostRequest`, `asyncGetRequest`, and `asyncGetRpcRequest` functions are asynchronous functions that make GET, POST, or RPC requests to a specified URL. They also support handling of response codes, raw responses, response results, nested JSON loading, and authorization.

Finally, the `async_get_response` is an asynchronous function that handles the response from an HTTP request. If the content type of the response is JSON, it attempts to extract the JSON content and, in case of decoding failure, it will return the raw text of the response.

Overall, this script enhances the abstract_apis module with the ability to manage, execute, and handle asynchronous HTTP requests.



-`make_request`
src/abstract_apis/make_request.py
The script provided, make_request.py, is part of the abstract_apis package and is found in the src/abstract_apis directory. It appears to be a utility script designed for making HTTP requests and handling the respective responses.

The script starts by importing request utilities from `abstract_apis.request_utils` and setting up a logging level to suppress logs below WARNING level using python's logging library.

The main function `make_request` is designed to carry out various types of HTTP requests – specifically GET and POST requests. It accepts a variety of parameters such as the request's URL, data, headers, endpoint, status code, retry_after period, raw response, response result data, loaded nested JSON responses, and authorization details. This function uses the Python `requests` library to carry out the actual HTTP requests, and its behavior is adjusted according to the specified parameters. If the HTTP method is not 'POST' or 'GET', the function raises a ValueError.

Furthermore, the script includes `getRpcData` which returns a dictionary with RPC request data, and two wrapper functions `postRequest` and `getRequest` that utilize `make_request` to perform respectively HTTP POST and GET requests. 

Overall, this script plays a fundamental role in the abstract_apis module by providing a mechanism to make HTTP requests and retrieve the data at specified endpoints.



-`request_utils`
src/abstract_apis/request_utils.py
The provided code chunk is a part of the request_utils.py script from the abstract_apis module. The script appears to provide several utility functions to facilitate the making and management of HTTP requests. The function `get_headers()` returns a dictionary containing a standard \'Content-Type\' header. The `ensure_json()` function verifies if the provided data is in JSON format and if not, it converts it into valid JSON string. The `stripit()` function is used to strip unwanted characters from strings. `make_endpoint()` and `make_url()` are helper functions used to format and clean up endpoint and URL strings respectively. `get_url()` constructs the URL by concatenating the base URL and the endpoint, after verifying and cleaning each. The `get_text_response()` function tries to access the text from a response object and returns it, if available. On failure, it simply returns None. These functions help in simplifying the construction of URLs and easier data handling.


## Installation
The module can be installed via pip. Ensure to have Python version 3.6 or above. The dependencies are `abstract_utilities` and `requests`.

```bash
pip install abstract_apis
```
## Dependencies
- `abstract_utilities`
- `requests`

## Usage
Typically, the module is imported in your Python script as follows:
```python
from import abstract_apis
```

Then, specific functions like GET or POST requests can be used as per the requirements.

## License
The project is licensed under the MIT License.

## Author
- Putkoff (partners@abstractendeavors.com)

## Contributions
Contributions to the project are welcome. Please refer to the module’s GitHub repository - [abstract APIs](https://github.com/AbstractEndeavors/abstract_apis)
=======
# Unknown Package (vUnknown Version)

No description available

## Installation

```bash
pip install Unknown Package
```

