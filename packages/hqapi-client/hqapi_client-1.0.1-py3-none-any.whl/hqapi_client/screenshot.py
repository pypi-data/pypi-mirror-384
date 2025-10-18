import requests
from typing import Optional, Dict, Any

class ScreenshotClientError(Exception):
    """Custom exception for ScreenshotClient API errors."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")

class ScreenshotClient:
    """
    Client for interacting with the Screenshot API.

    Methods:
        - create: Capture a screenshot of a website with customizable options.
        - nop: Test connectivity / no-operation endpoint.
    """

    BASE_URL = "https://api.eu-west.hqapi.com/api/v1"

    def __init__(self, token: str):
        """
        Initialize the ScreenshotClient with your API token.

        Args:
            token (str): Your API token.
        """
        self.token = token

    def create(
        self,
        url: str,
        theme: str = "light",
        browser_width: int = 1600,
        browser_height: int = 900,
        delay: int = 2500,
        output_format: str = "png",
        jpeg_quality: int = 95,
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
        mobile: bool = False,
        hide_cookie_popups: bool = False,
        full_page: bool = False,
    ) -> bytes:
        """
        Capture a screenshot of a website.

        Args:
            url (str): URL of the website to capture.
            theme (str): Browser theme ('light' or 'dark').
            browser_width (int): Width of the virtual browser.
            browser_height (int): Height of the virtual browser.
            delay (int): Delay in milliseconds after page load.
            output_format (str): Output image format ('png' or 'jpeg').
            jpeg_quality (int): JPEG quality (1-100), only used if format is 'jpeg'.
            image_width (Optional[int]): Resize width of the output image.
            image_height (Optional[int]): Resize height of the output image.
            mobile (bool): If true, emulate mobile browser.
            hide_cookie_popups (bool): Attempt to hide cookie popups.
            full_page (bool): Capture full page screenshot.

        Returns:
            bytes: Screenshot image content.
        """
        url_endpoint = f"{self.BASE_URL}/{self.token}/screenshot/create"

        payload: Dict[str, Any] = {
            "url": url,
            "theme": theme,
            "browser_width": browser_width,
            "browser_height": browser_height,
            "delay": delay,
            "format": output_format,
            "jpeg_quality": jpeg_quality,
            "mobile": mobile,
            "hide_cookie_popups": hide_cookie_popups,
            "full_page": full_page,
        }

        if image_width:
            payload["image_width"] = image_width
        if image_height:
            payload["image_height"] = image_height

        try:
            response = requests.post(url_endpoint, json=payload)
            response.raise_for_status()
            # Convert bytes to PIL Image
            return response.content
        except requests.exceptions.HTTPError as e:
            try:
                error_json = response.json()
                message = error_json.get("message", str(error_json))
            except ValueError:
                message = response.text
            raise ScreenshotClientError(response.status_code, message) from e

