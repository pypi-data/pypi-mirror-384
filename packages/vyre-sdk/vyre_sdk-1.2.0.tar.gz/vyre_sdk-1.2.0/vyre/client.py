"""
Vyre Python SDK Client
"""

import json
import requests
import asyncio
import aiohttp # pyright: ignore[reportMissingImports]
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin


class VyreException(Exception):
    """Base exception for Vyre SDK errors."""
    pass


class VyreAuthError(VyreException):
    """Authentication error."""
    pass


class VyreRateLimitError(VyreException):
    """Rate limit exceeded."""
    pass


class VyreAPIError(VyreException):
    """API error."""
    pass


class Vyre:
    """Vyre Python SDK client."""

    def __init__(self, api_key: str, base_url: str = "https://api.vyre.com/v1"):
        """
        Initialize Vyre client.

        Args:
            api_key: Your Vyre API key
            base_url: Base URL for the API (default: https://api.vyre.com/v1)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': f'vyre-python/{__import__("vyre").__version__}'
        })

    def chat(self, message: str, chat_id: Optional[str] = None,
             model: Optional[str] = None, file_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Send a chat message and get AI response.

        Args:
            message: The message to send
            chat_id: Optional conversation ID to continue a conversation
            model: Optional AI model to use
            file_ids: Optional list of file IDs to include

        Returns:
            Dict containing the AI response
        """
        data = {
            'message': message,
            'chat_id': chat_id,
            'model': model,
            'file_ids': file_ids
        }

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        try:
            response = self.session.post(
                urljoin(self.base_url, '/chat'),
                json=data
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            raise VyreAPIError(f"Request failed: {e}")

    def get_conversations(self) -> Dict[str, Any]:
        """
        Get list of user conversations.

        Returns:
            Dict containing conversations list
        """
        try:
            response = self.session.get(urljoin(self.base_url, '/conversations'))
            return self._handle_response(response)
        except requests.RequestException as e:
            raise VyreAPIError(f"Request failed: {e}")

    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation details and messages.

        Args:
            conversation_id: The conversation ID

        Returns:
            Dict containing conversation details
        """
        try:
            response = self.session.get(
                urljoin(self.base_url, f'/conversations/{conversation_id}')
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            raise VyreAPIError(f"Request failed: {e}")

    def upload_file(self, file_path: str, purpose: str = "assist") -> Dict[str, Any]:
        """
        Upload a file for processing.

        Args:
            file_path: Path to the file to upload
            purpose: Purpose of the upload (default: "assist")

        Returns:
            Dict containing file upload response
        """
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {'purpose': purpose}
                response = self.session.post(
                    urljoin(self.base_url, '/files'),
                    files=files,
                    data=data
                )
            return self._handle_response(response)
        except FileNotFoundError:
            raise VyreException(f"File not found: {file_path}")
        except requests.RequestException as e:
            raise VyreAPIError(f"Upload failed: {e}")

    def register_webhook(self, url: str, events: List[str], secret: str) -> Dict[str, Any]:
        """
        Register a webhook endpoint.

        Args:
            url: Webhook URL
            events: List of events to subscribe to
            secret: Webhook secret for verification

        Returns:
            Dict containing webhook registration response
        """
        data = {
            'url': url,
            'events': events,
            'secret': secret
        }

        try:
            response = self.session.post(
                urljoin(self.base_url, '/webhooks'),
                json=data
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            raise VyreAPIError(f"Request failed: {e}")

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {'error': 'Invalid JSON response'}

        if response.status_code == 401:
            raise VyreAuthError("Invalid API key")
        elif response.status_code == 429:
            raise VyreRateLimitError("Rate limit exceeded")
        elif not response.ok:
            error_msg = data.get('error', f"API error: {response.status_code}")
            raise VyreAPIError(error_msg)

        return data


class AsyncVyre:
    """Async version of Vyre client."""

    def __init__(self, api_key: str, base_url: str = "https://api.vyre.com/v1"):
        """
        Initialize async Vyre client.

        Args:
            api_key: Your Vyre API key
            base_url: Base URL for the API (default: https://api.vyre.com/v1)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': f'vyre-python-async/{__import__("vyre").__version__}'
        }

    async def chat(self, message: str, chat_id: Optional[str] = None,
                   model: Optional[str] = None, file_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Send a chat message and get AI response asynchronously.

        Args:
            message: The message to send
            chat_id: Optional conversation ID to continue a conversation
            model: Optional AI model to use
            file_ids: Optional list of file IDs to include

        Returns:
            Dict containing the AI response
        """
        data = {
            'message': message,
            'chat_id': chat_id,
            'model': model,
            'file_ids': file_ids
        }

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.post(
                    urljoin(self.base_url, '/chat'),
                    json=data
                ) as response:
                    return await self._handle_response(response)
            except aiohttp.ClientError as e:
                raise VyreAPIError(f"Request failed: {e}")

    async def get_conversations(self) -> Dict[str, Any]:
        """
        Get list of user conversations asynchronously.

        Returns:
            Dict containing conversations list
        """
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(urljoin(self.base_url, '/conversations')) as response:
                    return await self._handle_response(response)
            except aiohttp.ClientError as e:
                raise VyreAPIError(f"Request failed: {e}")

    async def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation details and messages asynchronously.

        Args:
            conversation_id: The conversation ID

        Returns:
            Dict containing conversation details
        """
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(
                    urljoin(self.base_url, f'/conversations/{conversation_id}')
                ) as response:
                    return await self._handle_response(response)
            except aiohttp.ClientError as e:
                raise VyreAPIError(f"Request failed: {e}")

    async def register_webhook(self, url: str, events: List[str], secret: str) -> Dict[str, Any]:
        """
        Register a webhook endpoint asynchronously.

        Args:
            url: Webhook URL
            events: List of events to subscribe to
            secret: Webhook secret for verification

        Returns:
            Dict containing webhook registration response
        """
        data = {
            'url': url,
            'events': events,
            'secret': secret
        }

        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.post(
                    urljoin(self.base_url, '/webhooks'),
                    json=data
                ) as response:
                    return await self._handle_response(response)
            except aiohttp.ClientError as e:
                raise VyreAPIError(f"Request failed: {e}")

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle async API response and raise appropriate exceptions."""
        try:
            data = await response.json()
        except aiohttp.ContentTypeError:
            data = {'error': 'Invalid JSON response'}

        if response.status == 401:
            raise VyreAuthError("Invalid API key")
        elif response.status == 429:
            raise VyreRateLimitError("Rate limit exceeded")
        elif not response.ok:
            error_msg = data.get('error', f"API error: {response.status}")
            raise VyreAPIError(error_msg)

        return data
