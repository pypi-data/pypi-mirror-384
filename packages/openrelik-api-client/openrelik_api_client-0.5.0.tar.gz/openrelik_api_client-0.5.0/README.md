## OpenRelik API Client

This Python package provides a simple API client (`APIClient`) that automatically handles token refresh on 401 (Unauthorized) responses.

* **Automatic token refresh:** Seamlessly refreshes expired access tokens using a refresh token.
* **Easy-to-use interface:** Simple methods for common HTTP requests (GET, POST, PUT, DELETE).
* **Customizable:**  Allows you to specify the API server URL, API key, and API version.

## Installation

   ```bash
   pip install openrelik-api-client
   ```

**Example:**
   ```python
    import os
    from openrelik_api_client.api_client import APIClient

    # Initialize the API client
    api_server_url = "http://localhost:8710"

    # API key from environment variable
    api_key = os.getenv("OPENRELIK_API_KEY")

    # Create the API client. It will handle token refreshes automatically.
    api_client = APIClient(api_server_url, api_key)

    # Example GET request
    response = api_client.get("/users/me/")
    print(response.json())
```


**How it works:**

The `APIClient` utilizes a custom session class (`TokenRefreshSession`) that intercepts requests and checks for 401 responses. If a 401 response is encountered, it automatically attempts to refresh the access token using the provided refresh token. If the refresh is successful, the original request is retried with the new access token.

##### Obligatory Fine Print
This is not an official Google product (experimental or otherwise), it is just code that happens to be owned by Google.
