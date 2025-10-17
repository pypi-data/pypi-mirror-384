"""Speaker Manager

HTTP API-based asynchronous speaker management functionality.
Provides comprehensive speaker CRUD operations with robust error handling.
"""

import asyncio
import logging
from typing import Any
from urllib.parse import urljoin

import aiohttp

from ..models.speaker import (
    CreateSpeakerRequest,
    SpeakerInfo,
    SpeakerResponse,
    UpdateSpeakerRequest,
)
from ..utils.exceptions import (
    ConnectionError,
    SpeakerError,
    TimeoutError,
    ValidationError,
)
from ..utils.validation import (
    validate_speaker_id,
    validate_text_content,
    validate_url,
)

logger = logging.getLogger(__name__)


class SpeakerManager:
    """Asynchronous speaker manager with comprehensive CRUD operations.

    This class provides speaker creation, query, update, and deletion
    management functions using HTTP API endpoints.

    Features:
    - Asynchronous operations with proper connection management
    - Automatic retry mechanism for failed requests
    - Comprehensive error handling and logging
    - Context manager support for resource cleanup

    Example:
        async with SpeakerManager(server_url, api_key) as manager:
            speaker = await manager.create(
                prompt_text="Hello world",
                prompt_audio_path="https://example.com/audio.wav"
            )
    """

    # Default configuration constants
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0

    # HTTP client configuration
    CONNECTION_LIMIT = 100
    DNS_CACHE_TTL = 300

    def __init__(
        self,
        server_url: str,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ) -> None:
        """Initialize the speaker manager.

        Args:
            server_url: Base URL of the speaker management service
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            retry_delay: Base delay between retry attempts in seconds

        Raises:
            ValidationError: If server_url is invalid
        """
        self.server_url = self._normalize_server_url(server_url)
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # HTTP client session management
        self._session: aiohttp.ClientSession | None = None
        self._session_lock = asyncio.Lock()

        logger.info(f"Initialized SpeakerManager for {self.server_url}")

    def _normalize_server_url(self, url: str) -> str:
        """Normalize and validate server URL.

        Converts WebSocket URLs to HTTP and ensures proper formatting.

        Args:
            url: Raw server URL

        Returns:
            Normalized HTTP URL

        Raises:
            ValidationError: If URL format is invalid
        """
        validate_url(url)

        # Convert WebSocket URLs to HTTP equivalents
        url_mappings = {
            'wss://': 'https://',
            'ws://': 'http://'
        }

        for ws_scheme, http_scheme in url_mappings.items():
            if url.startswith(ws_scheme):
                url = url.replace(ws_scheme, http_scheme)
                break

        # Remove WebSocket-specific paths
        if url.endswith('/ws/tts'):
            url = url[:-7]

        # Ensure URL ends with slash for proper joining
        if not url.endswith('/'):
            url += '/'

        return url

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with proper configuration.

        Creates a new session if none exists or if the current session is closed.
        Uses double-checked locking pattern for thread safety.

        Returns:
            Configured aiohttp ClientSession
        """
        if self._session is None or self._session.closed:
            async with self._session_lock:
                if self._session is None or self._session.closed:
                    self._session = await self._create_session()

        return self._session

    async def _create_session(self) -> aiohttp.ClientSession:
        """Create a new HTTP session with optimal configuration.

        Returns:
            Configured aiohttp ClientSession
        """
        # Configure connection pooling and timeouts
        connector = aiohttp.TCPConnector(
            limit=self.CONNECTION_LIMIT,
            ttl_dns_cache=self.DNS_CACHE_TTL
        )
        timeout = aiohttp.ClientTimeout(total=self.timeout)

        # Set default headers
        headers = self._build_default_headers()

        return aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )

    def _build_default_headers(self) -> dict[str, str]:
        """Build default HTTP headers for all requests.

        Returns:
            Dictionary of default headers
        """
        headers = {
            'User-Agent': 'CosyVoice-Python-SDK/1.0.0',
            'Content-Type': 'application/json'
        }

        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        return headers

    async def close(self) -> None:
        """Close the HTTP session and cleanup resources.

        Should be called when the manager is no longer needed.
        Automatically called when used as a context manager.
        """
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("HTTP session closed")

    # CRUD Operations

    async def create(
        self,
        prompt_text: str,
        prompt_audio_path: str,
        zero_shot_spk_id: str | None = None,
    ) -> SpeakerInfo:
        """Create a new speaker with specified parameters.

        Args:
            prompt_text: Reference text for voice cloning
            prompt_audio_path: URL to reference audio file
            zero_shot_spk_id: Custom speaker ID (auto-generated if None)

        Returns:
            SpeakerInfo object containing created speaker details

        Raises:
            ValidationError: If input parameters are invalid
            SpeakerError: If speaker creation fails

        Example:
            speaker = await manager.create(
                prompt_text="Hello world",
                prompt_audio_path="https://example.com/audio.wav",
                zero_shot_spk_id="my_speaker"
            )
        """
        # Validate input parameters
        self._validate_create_params(prompt_text, zero_shot_spk_id)

        # Build request object
        request = CreateSpeakerRequest(
            prompt_text=prompt_text,
            zero_shot_spk_id=zero_shot_spk_id,
            prompt_audio_path=prompt_audio_path
        )

        try:
            # Send creation request
            response = await self._send_create_request(request)

            # Validate and extract speaker info
            speaker_info = self._extract_speaker_info(response, "create")

            logger.info(
                f"Speaker created successfully: {speaker_info.zero_shot_spk_id}")
            return speaker_info

        except SpeakerError:
            raise
        except Exception as e:
            raise SpeakerError(
                f"Unexpected error creating speaker: {e}") from e

    async def get_info(self, zero_shot_spk_id: str) -> SpeakerInfo:
        """Retrieve detailed information about a specific speaker.

        Args:
            zero_shot_spk_id: Unique identifier of the speaker

        Returns:
            SpeakerInfo object with speaker details

        Raises:
            ValidationError: If speaker ID format is invalid
            SpeakerError: If speaker not found or retrieval fails

        Example:
            speaker_info = await manager.get_info("my_speaker")
            print(f"Speaker: {speaker_info.zero_shot_spk_id}")
        """
        validate_speaker_id(zero_shot_spk_id)

        try:
            url = urljoin(self.server_url, f"speakers/{zero_shot_spk_id}")
            data = await self._make_request("GET", url)

            # Handle different response formats
            return self._parse_speaker_response(data)

        except SpeakerError:
            raise
        except Exception as e:
            raise SpeakerError(
                f"Failed to get speaker information: {e}") from e

    async def update(
        self,
        zero_shot_spk_id: str,
        prompt_text: str | None = None,
        prompt_audio_path: str | None = None,
    ) -> SpeakerInfo:
        """Update an existing speaker's parameters.

        Args:
            zero_shot_spk_id: Unique identifier of the speaker to update
            prompt_text: New reference text (optional)
            prompt_audio_path: New reference audio URL (optional)

        Returns:
            SpeakerInfo object with updated speaker details

        Raises:
            ValidationError: If parameters are invalid
            SpeakerError: If speaker not found or update fails

        Example:
            updated_speaker = await manager.update(
                zero_shot_spk_id="my_speaker",
                prompt_text="New reference text"
            )
        """
        validate_speaker_id(zero_shot_spk_id)
        self._validate_update_params(prompt_text)

        # Build request object
        request = UpdateSpeakerRequest(
            prompt_text=prompt_text,
            prompt_audio_path=prompt_audio_path
        )

        try:
            # Send update request
            response = await self._send_update_request(zero_shot_spk_id, request)

            # Validate and extract speaker info
            speaker_info = self._extract_speaker_info(response, "update")

            logger.info(f"Speaker updated successfully: {zero_shot_spk_id}")
            return speaker_info

        except SpeakerError:
            raise
        except Exception as e:
            raise SpeakerError(
                f"Unexpected error updating speaker: {e}") from e

    async def delete(self, zero_shot_spk_id: str) -> bool:
        """Delete a speaker permanently.

        Args:
            zero_shot_spk_id: Unique identifier of the speaker to delete

        Returns:
            True if deletion was successful

        Raises:
            ValidationError: If speaker ID format is invalid
            SpeakerError: If speaker not found or deletion fails

        Example:
            success = await manager.delete("my_speaker")
            if success:
                print("Speaker deleted successfully")
        """
        validate_speaker_id(zero_shot_spk_id)

        try:
            url = urljoin(self.server_url, f"speakers/{zero_shot_spk_id}")
            data = await self._make_request("DELETE", url)

            # Parse response
            speaker_response = SpeakerResponse(**data)

            if not speaker_response.is_success:
                error_msg = self._build_error_message(
                    "Speaker deletion failed",
                    speaker_response.error
                )
                raise SpeakerError(
                    error_msg,
                    error_code="SPEAKER_DELETE_FAILED",
                    details=speaker_response.error or {}
                )

            logger.info(f"Speaker deleted successfully: {zero_shot_spk_id}")
            return True

        except SpeakerError:
            raise
        except Exception as e:
            raise SpeakerError(
                f"Unexpected error deleting speaker: {e}") from e

    async def exists(self, zero_shot_spk_id: str) -> bool:
        """Check if a speaker exists in the system.

        Args:
            zero_shot_spk_id: Unique identifier of the speaker to check

        Returns:
            True if speaker exists, False otherwise

        Raises:
            SpeakerError: If check operation fails (not including "not found")

        Example:
            if await manager.exists("my_speaker"):
                print("Speaker exists")
            else:
                print("Speaker not found")
        """
        try:
            url = urljoin(self.server_url, f"speakers/{zero_shot_spk_id}")
            data = await self._make_request("GET", url)

            # Check response for existence
            if isinstance(data, dict) and 'is_success' in data:
                speaker_response = SpeakerResponse(**data)
                if not speaker_response.is_success and speaker_response.error:
                    error_code = speaker_response.error.get('code')
                    if error_code == 'COSYVOICE_NOT_FOUND_SPEAKER':
                        return False

            # If we get here, speaker exists
            return True

        except SpeakerError as e:
            # Check if it's a "not found" error
            if 'COSYVOICE_NOT_FOUND_SPEAKER' in str(
                    e) or 'Speaker not found' in str(e):
                return False
            # Re-raise other errors
            raise

    # Validation helpers

    def _validate_create_params(
            self,
            prompt_text: str,
            zero_shot_spk_id: str | None) -> None:
        """Validate parameters for speaker creation.

        Args:
            prompt_text: Reference text to validate
            zero_shot_spk_id: Speaker ID to validate (if provided)

        Raises:
            ValidationError: If any parameter is invalid
        """
        validate_text_content(prompt_text)
        if zero_shot_spk_id is not None:
            validate_speaker_id(zero_shot_spk_id)

    def _validate_update_params(self, prompt_text: str | None) -> None:
        """Validate parameters for speaker update.

        Args:
            prompt_text: Reference text to validate (if provided)

        Raises:
            ValidationError: If prompt_text is invalid
        """
        if prompt_text is not None:
            validate_text_content(prompt_text)

    # Request helpers

    async def _send_create_request(
            self, request: CreateSpeakerRequest) -> SpeakerResponse:
        """Send speaker creation request to the server.

        Args:
            request: Validated creation request object

        Returns:
            Server response as SpeakerResponse object
        """
        url = urljoin(self.server_url, "speakers")
        data = request.model_dump(exclude_none=True)

        response_data = await self._make_request("POST", url, json=data)
        return SpeakerResponse(**response_data)

    async def _send_update_request(
        self,
        zero_shot_spk_id: str,
        request: UpdateSpeakerRequest
    ) -> SpeakerResponse:
        """Send speaker update request to the server.

        Args:
            zero_shot_spk_id: Speaker ID to update
            request: Validated update request object

        Returns:
            Server response as SpeakerResponse object
        """
        url = urljoin(self.server_url, f"speakers/{zero_shot_spk_id}")
        data = request.model_dump(exclude_none=True)

        response_data = await self._make_request("PUT", url, json=data)
        return SpeakerResponse(**response_data)

    # Response parsing helpers

    def _extract_speaker_info(
            self,
            response: SpeakerResponse,
            operation: str) -> SpeakerInfo:
        """Extract and validate speaker info from server response.

        Args:
            response: Server response object
            operation: Type of operation (for error messages)

        Returns:
            Validated SpeakerInfo object

        Raises:
            SpeakerError: If response indicates failure or is invalid
        """
        if not response.is_success:
            error_msg = self._build_error_message(
                f"Speaker {operation} failed",
                response.error
            )
            raise SpeakerError(
                error_msg,
                error_code=f"SPEAKER_{operation.upper()}_FAILED",
                details=response.error or {}
            )

        if not response.speaker_info:
            raise SpeakerError(f"No speaker info in {operation} response")

        return SpeakerInfo(**response.speaker_info)

    def _parse_speaker_response(self, data: dict[str, Any]) -> SpeakerInfo:
        """Parse speaker response data into SpeakerInfo object.

        Handles both direct SpeakerInfo format and wrapped SpeakerResponse format.

        Args:
            data: Raw response data from server

        Returns:
            Parsed SpeakerInfo object

        Raises:
            SpeakerError: If response format is invalid or indicates failure
        """
        # Handle wrapped response format
        if isinstance(data, dict) and 'is_success' in data:
            speaker_response = SpeakerResponse(**data)
            if speaker_response.is_success and speaker_response.speaker_info:
                return SpeakerInfo(**speaker_response.speaker_info)
            else:
                raise SpeakerError("Failed to get speaker info")

        # Handle direct SpeakerInfo format
        return SpeakerInfo(**data)

    def _build_error_message(
            self, base_msg: str, error_data: dict[str, Any] | None) -> str:
        """Build comprehensive error message from server error data.

        Args:
            base_msg: Base error message
            error_data: Error details from server response

        Returns:
            Formatted error message
        """
        if error_data and isinstance(error_data, dict):
            message = error_data.get('message', 'Unknown error')
            return f"{base_msg}: {message}"
        return base_msg

    # Low-level HTTP operations

    async def _make_request(
        self,
        method: str,
        url: str,
        **kwargs: Any
    ) -> dict[str, Any]:
        """Send HTTP request and handle response with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Target URL
            **kwargs: Additional request parameters

        Returns:
            Parsed JSON response data

        Raises:
            ConnectionError: If all retry attempts fail
            TimeoutError: If request times out
            SpeakerError: If response handling fails
        """
        session = await self._get_session()

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(
                    f"Sending request: {method} {url} (attempt {attempt + 1})")
                if 'json' in kwargs:
                    logger.debug(f"Request data: {kwargs['json']}")

                async with session.request(method, url, **kwargs) as response:
                    logger.debug(
                        f"Request completed: {method} {url} -> {response.status}")

                    # Check for server errors that should be retried
                    if response.status >= 500:
                        if attempt == self.max_retries:
                            # For 5xx errors, try to read response for better
                            # error info
                            try:
                                error_text = await response.text()
                                logger.error(
                                    f"Server error response: {error_text}")
                            except Exception:
                                pass
                            raise ConnectionError(
                                f"Server error: {response.status} {response.reason}")
                        else:
                            logger.warning(
                                f"Server error {response.status}, retrying (attempt {attempt + 1})")
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                            continue

                    # Handle response within context manager
                    try:
                        return await self._handle_response(response)
                    except Exception as e:
                        # If handling fails and we can retry, do so
                        if attempt < self.max_retries:
                            logger.warning(
                                f"Response handling failed, retrying (attempt {attempt + 1}): {e}")
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                            continue
                        else:
                            raise

            except asyncio.TimeoutError as e:
                logger.warning(
                    f"Request timeout (attempt {attempt + 1}): {method} {url}")
                if attempt == self.max_retries:
                    raise TimeoutError(
                        f"Request timeout: {method} {url}") from e
                await asyncio.sleep(self.retry_delay * (attempt + 1))

            except aiohttp.ClientError as e:
                logger.warning(
                    f"Request failed (attempt {attempt + 1}): {method} {url} - {e}")
                if attempt == self.max_retries:
                    raise ConnectionError(f"Request failed: {e}") from e
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        # This should never be reached due to exceptions being raised above
        raise ConnectionError(f"All retry attempts failed for {method} {url}")

    async def _handle_response(
            self, response: aiohttp.ClientResponse) -> dict[str, Any]:
        """Handle HTTP response and extract JSON data.

        Args:
            response: aiohttp response object

        Returns:
            Parsed JSON response data

        Raises:
            SpeakerError: If response handling fails
            ValidationError: If request parameters were invalid
        """
        try:
            logger.debug(f"Response status: {response.status}")
            logger.debug(f"Response headers: {dict(response.headers)}")

            # Read response text for debugging and parsing
            try:
                response_text = await response.text()
                logger.debug(f"Response text: {response_text[:500]}...")
            except Exception as text_err:
                logger.error(f"Failed to read response text: {text_err}")
                raise SpeakerError(
                    f"Failed to read response from server: {text_err}") from text_err

            # Handle different status codes
            if response.status == 200:
                return await self._parse_success_response(response, response_text)
            elif response.status == 400:
                raise await self._parse_validation_error(response, response_text)
            elif response.status == 404:
                raise SpeakerError(
                    "Resource not found",
                    error_code="RESOURCE_NOT_FOUND")
            elif response.status == 429:
                raise SpeakerError(
                    "Too many requests",
                    error_code="RATE_LIMIT_EXCEEDED")
            elif response.status == 503:
                raise SpeakerError(
                    "Service temporarily unavailable. The server may be under maintenance or overloaded.",
                    error_code="SERVICE_UNAVAILABLE")
            else:
                error_msg = f"Unknown response status code: {response.status}"
                if response_text:
                    error_msg += f" - Response: {response_text}"
                raise SpeakerError(error_msg)

        except SpeakerError:
            raise
        except Exception as e:
            error_msg = f"Error handling response: {e}"
            logger.error(error_msg)
            logger.error(f"Response status: {response.status}")
            logger.error(f"Response headers: {dict(response.headers)}")
            raise SpeakerError(error_msg) from e

    async def _parse_success_response(
        self,
        response: aiohttp.ClientResponse,
        response_text: str
    ) -> dict[str, Any]:
        """Parse successful (200) response.

        Args:
            response: aiohttp response object
            response_text: Response body text

        Returns:
            Parsed JSON data

        Raises:
            SpeakerError: If response is empty or invalid JSON
        """
        if not response_text.strip():
            logger.error("Empty response body from server")
            raise SpeakerError("Empty response from server")

        try:
            json_data = await response.json()
            if not isinstance(json_data, dict):
                raise SpeakerError("Invalid response format: expected JSON object")
            return json_data
        except Exception as json_err:
            logger.error(f"Failed to parse JSON response: {json_err}")
            logger.error(f"Response text: {response_text}")
            raise SpeakerError(
                f"Invalid JSON response: {response_text}") from json_err

    async def _parse_validation_error(
        self,
        response: aiohttp.ClientResponse,
        response_text: str
    ) -> ValidationError:
        """Parse validation error (400) response.

        Args:
            response: aiohttp response object
            response_text: Response body text

        Returns:
            ValidationError with appropriate message
        """
        if response_text:
            try:
                error_data = await response.json()
                message = error_data.get('message', 'Unknown error')
                return ValidationError(
                    f"Invalid request parameters: {message}")
            except Exception:
                return ValidationError(
                    f"Invalid request parameters: {response_text}")
        else:
            return ValidationError("Invalid request parameters: Bad Request")

    # Context manager support

    async def __aenter__(self) -> 'SpeakerManager':
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager and cleanup resources."""
        await self.close()
