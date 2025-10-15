# src/vision_browser_sdk/exceptions.py

class VisionAPIError(Exception):
    """Base exception for all errors related to the Vision API."""
    pass


class VisionAPIRequestError(VisionAPIError):
    """
    Raised when the API returns an unsuccessful HTTP status code (4xx or 5xx).
    """

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = f"API request failed with status {status_code}: {message}"
        super().__init__(self.message)
