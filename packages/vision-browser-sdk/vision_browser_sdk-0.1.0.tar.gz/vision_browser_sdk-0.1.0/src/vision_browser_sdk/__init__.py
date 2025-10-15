# src/vision_browser_sdk/__init__.py

from .client import AsyncVisionBrowserClient, VisionBrowserClient
from .exceptions import VisionAPIError, VisionAPIRequestError
from .models import *

__all__ = [
    # --- Clients ---
    "VisionBrowserClient",
    "AsyncVisionBrowserClient",

    # --- Exceptions ---
    "VisionAPIError",
    "VisionAPIRequestError",

    # --- Models ---

    # Folder Models
    "Folder",
    "CreateFolderPayload",
    "UpdateFolderPayload",

    # Profile & Fingerprint Models
    "Profile",
    "ProfileList",
    "Fingerprint",
    "Screen",
    "Hints",
    "Navigator",
    "CreateProfilePayload",
    "UpdateProfilePayload",
    "FingerprintData",

    # Cookie Models
    "Cookie",
    "ImportCookiesPayload",

    # Proxy Models
    "Proxy",
    "CreateProxyPayload",
    "CreateProxyItem",  # Важная модель для создания прокси
    "UpdateProxyPayload",
    "DeleteProxyPayload",

    # Status Models
    "Status",
    "CreateStatusesPayload",
    "UpdateStatusPayload",
    "DeleteStatusesPayload",

    # Tag Models
    "Tag",
    "CreateTagsPayload",
    "UpdateTagPayload",
    "DeleteTagsPayload",

    # Local API Models
    "RunningProfile",
    "RunningProfileInfo",
    "StartProfilePayload",
    "TempProxy",
]
