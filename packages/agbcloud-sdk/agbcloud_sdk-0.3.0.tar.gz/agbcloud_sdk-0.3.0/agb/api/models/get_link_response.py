# -*- coding: utf-8 -*-
"""
Get link response model for HTTP client
"""

from typing import Any, Dict, Optional


class GetLinkResponse:
    """
    Response model for getting session link
    """

    def __init__(
        self,
        status_code: Optional[int] = None,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        self.status_code = status_code
        self.url = url
        self.headers = headers or {}
        self.json_data = json_data
        self.text = text
        self.success = success
        self.error = error
        self.request_id = request_id

        if json_data:
            self.api_success = json_data.get("success")
            self.code = json_data.get("code")
            self.message = json_data.get("message")
            self.http_status_code = json_data.get("httpStatusCode")
            self.url_data = (
                json_data.get("data", {}).get("url") if json_data.get("data") else None
            )
        else:
            self.api_success = None
            self.code = None
            self.message = None
            self.http_status_code = None
            self.url_data = None

    @classmethod
    def from_http_response(cls, response_dict: Dict[str, Any]) -> "GetLinkResponse":
        """
        Create GetLinkResponse from HTTP response dictionary

        Args:
            response_dict: HTTP response dictionary

        Returns:
            GetLinkResponse: Response object
        """
        json_data = response_dict.get("json", {})
        return cls(
            status_code=response_dict.get("status_code", 0),
            url=response_dict.get("url", ""),
            headers=response_dict.get("headers", {}),
            success=response_dict.get("success", False),
            json_data=json_data,
            text=response_dict.get("text"),
            error=response_dict.get("error"),
            request_id=response_dict.get("request_id")
            or (
                response_dict.get("json", {}).get("requestId", "")
                if response_dict.get("json")
                else None
            ),
        )

    def is_successful(self) -> bool:
        """
        Check if the response indicates success

        Returns:
            bool: True if successful, False otherwise
        """
        return self.success and self.status_code == 200 and self.api_success is True

    def get_error_message(self) -> Optional[str]:
        """
        Get error message if response failed

        Returns:
            Optional[str]: Error message or None if successful
        """
        return self.error if not self.is_successful() else None

    def get_url(self) -> Optional[str]:
        """
        Get the URL from response

        Returns:
            Optional[str]: URL or None if not found
        """
        return self.url_data if self.is_successful() else None


