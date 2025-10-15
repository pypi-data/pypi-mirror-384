
# Vision Browser SDK 

[![PyPI Version](https://img.shields.io/pypi/v/vision-browser-sdk.svg?style=flat-square)](https://pypi.org/project/vision-browser-sdk/)
[![Python Versions](https://img.shields.io/pypi/pyversions/vision-browser-sdk.svg?style=flat-square)](https://pypi.org/project/vision-browser-sdk/)
[![License](https://img.shields.io/pypi/l/vision-browser-sdk.svg?style=flat-square)](https://github.com/your-username/vision-browser-sdk/blob/main/LICENSE)
[![Build Status](https://img.shields.io/github/actions/workflow/status/your-username/vision-browser-sdk/publish.yml?style=flat-square)](https://github.com/your-username/vision-browser-sdk/actions)

**A modern, fully-typed, sync & async Python SDK for the [Vision Browser API](https://docs.browser.vision/).**

This library provides a clean, robust, and developer-friendly interface to manage browser profiles, folders, proxies, and other entities. It's designed from the ground up to offer a superior developer experience with powerful features like data validation and IDE auto-completion, saving you time and preventing bugs.

---

## ✅ Why Vision Browser SDK?

While other simple wrappers exist, this SDK is built on a professional architecture that solves common frustrations:

-   **Sync & Async out of the box**: Use a familiar synchronous client for simple scripts or a high-performance asynchronous client for modern applications with `asyncio`. The choice is yours, the API is identical.
-   **Pydantic-Powered Data**: No more guessing dictionary keys (`['profile_name']`) or dealing with unexpected `None` values. All API responses are parsed into robust Pydantic models, giving you:
    -   **Powerful IDE auto-completion**: Write code faster and with fewer errors.
    -   **Automatic data validation**: Get clear errors if the API returns an unexpected response.
    -   **Self-documenting code**: The models themselves define the data structures.
-   **Clean, Intuitive API**: A logical, service-based architecture (`client.folders.list()`, `client.profiles.create(...)`) makes the SDK easy to learn and a pleasure to use.
-   **Robust Error Handling**: Custom, meaningful exceptions for handling API and network errors gracefully.
-   **Zero Code Duplication**: A smart internal design provides both sync and async capabilities without duplicating logic, ensuring the library is maintainable and reliable.

## 🚀 Installation

The library requires Python 3.8 or newer.

```bash
pip install vision-browser-sdk

##  quickstart

Get your API token from the Vision Browser application settings. It is highly recommended to store it as an environment variable rather than hardcoding it in your scripts.

Create a `.env` file in your project root:

VISION_API_TOKEN="your_real_api_token_here"
```

### Synchronous Usage

Perfect for standard scripts and automation tasks.

```python
import os
from dotenv import load_dotenv
from vision_browser_sdk import VisionBrowserClient, CreateFolderPayload
from vision_browser_sdk.exceptions import VisionAPIError

# Load token from .env file
load_dotenv()
API_TOKEN = os.getenv("VISION_API_TOKEN")

if not API_TOKEN:
    raise ValueError("API token not found. Please set VISION_API_TOKEN in your .env file.")

# The client should be used as a context manager to handle sessions gracefully.
try:
    with VisionBrowserClient(token=API_TOKEN) as client:
        print("--- Testing Sync Client ---")
        
        # 1. List all folders
        print("1. Listing folders...")
        folders = client.folders.list()
        print(f"Found {len(folders)} folders.")
        for folder in folders:
            print(f" - Folder: '{folder.folder_name}', ID: {folder.id}")

        # 2. Create a new folder
        print("\n2. Creating a test folder...")
        payload = CreateFolderPayload(
            folder_name="[SDK] Sync Test Folder",
            folder_icon="Cloud",
            folder_color="#FFC1073D"
        )
        new_folder = client.folders.create(payload)
        print(f"Created folder '{new_folder.folder_name}'")

        # 3. Clean up by deleting the folder
        print("\n3. Deleting the test folder...")
        client.folders.delete(new_folder.id)
        print("Folder deleted successfully.")

except VisionAPIError as e:
    print(f"An API error occurred: {e}")
```

### Asynchronous Usage

Ideal for high-performance applications using `asyncio`, such as web servers or complex crawlers.

```python
import os
import asyncio
from dotenv import load_dotenv
from vision_browser_sdk import AsyncVisionBrowserClient
from vision_browser_sdk.exceptions import VisionAPIError

load_dotenv()
API_TOKEN = os.getenv("VISION_API_TOKEN")

async def main():
    if not API_TOKEN:
        raise ValueError("API token not found.")

    try:
        async with AsyncVisionBrowserClient(token=API_TOKEN) as client:
            print("--- Testing Async Client ---")

            # 1. List folders asynchronously
            print("1. Listing folders...")
            folders = await client.folders.list()
            print(f"Found {len(folders)} folders.")
            
            # 2. Get running profiles
            print("\n2. Checking for running profiles...")
            running_profiles = await client.get_running_profiles()
            if not running_profiles:
                print("No profiles are currently running.")
            else:
                for profile in running_profiles:
                    print(f" - Profile {profile.profile_id} is running on port {profile.port}")

    except VisionAPIError as e:
        print(f"An API error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

The client is organized into logical services.

-   `client.folders`
    -   `.list()`
    -   `.create(payload)`
    -   `.update(folder_id, payload)`
    -   `.delete(folder_id)`
-   `client.profiles`
    -   `.list(folder_id)`
    -   `.get_info(folder_id, profile_id)`
    -   `.create(folder_id, payload)`
    -   `.update(folder_id, profile_id, payload)`
    -   `.delete(folder_id, profile_id)`
    -   `.get_fingerprint(platform, version)`
    -   `.import_cookies(folder_id, profile_id, payload)`
    -   `.export_cookies(folder_id, profile_id)`
-   `client.proxies`
-   `client.statuses`
-   `client.tags`

### Local API (Start/Stop Profiles)

The client also provides direct access to the local API for controlling browser profiles.

```python
# Synchronous example
with VisionBrowserClient(token=API_TOKEN) as client:
    # This requires the Vision app to be running
    running_info = client.start_profile(folder_id="...", profile_id="...")
    print(f"Profile started! Connect on port {running_info.port}")
    
    client.stop_profile(folder_id="...", profile_id="...")
    print("Profile stopped.")
```

## Error Handling

The library raises custom exceptions to make error handling simple and predictable.

```python
from vision_browser_sdk import VisionBrowserClient
from vision_browser_sdk.exceptions import VisionAPIRequestError, VisionAPIError

try:
    with VisionBrowserClient(token="invalid-token") as client:
        client.folders.list()
except VisionAPIRequestError as e:
    # This catches specific HTTP errors from the API (4xx, 5xx)
    print(f"HTTP Error {e.status_code}: {e.message}")
except VisionAPIError as e:
    # This is a general catch-all for other library-related errors
    print(f"A general error occurred: {e}")
```

## 🤝 Contributing

Contributions are welcome! Whether it's a bug report, a feature request, or a pull request, we appreciate your help.

To set up a development environment:
1.  Clone the repository.
2.  Install [Poetry](https://python-poetry.org/docs/#installation).
3.  Run `poetry install` to create a virtual environment and install dependencies.
4.  Activate the pre-commit hooks with `pre-commit install`. This will automatically format and lint your code on every commit.
5.  Run tests with `poetry run pytest`.

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.