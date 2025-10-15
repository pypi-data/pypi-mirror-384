from typing import Optional

import aiohttp

from . import conf
from .exceptions import (
    BadRequestError,
    InternalServerError,
    NotFoundError,
    PaymentRequiredError,
    TypecastError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from .models import TTSRequest, TTSResponse, VoicesResponse


class AsyncTypecast:
    def __init__(self, host: Optional[str] = None, api_key: Optional[str] = None):
        self.host = conf.get_host(host)
        self.api_key = conf.get_api_key(api_key)
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        self.session = aiohttp.ClientSession(headers=headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _handle_error(self, status_code: int, response_text: str):
        """Handle HTTP error responses with specific exception types"""
        if status_code == 400:
            raise BadRequestError(f"Bad request: {response_text}")
        elif status_code == 401:
            raise UnauthorizedError(f"Unauthorized: {response_text}")
        elif status_code == 402:
            raise PaymentRequiredError(f"Payment required: {response_text}")
        elif status_code == 404:
            raise NotFoundError(f"Not found: {response_text}")
        elif status_code == 422:
            raise UnprocessableEntityError(f"Validation error: {response_text}")
        elif status_code == 500:
            raise InternalServerError(f"Internal server error: {response_text}")
        else:
            raise TypecastError(
                f"API request failed: {status_code}, {response_text}",
                status_code=status_code,
            )

    async def text_to_speech(self, request: TTSRequest) -> TTSResponse:
        if not self.session:
            raise TypecastError("Client session not initialized. Use async with.")
        endpoint = "/v1/text-to-speech"
        async with self.session.post(
            f"{self.host}{endpoint}", json=request.model_dump(exclude_none=True)
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                self._handle_error(response.status, error_text)

            audio_data = await response.read()
            return TTSResponse(
                audio_data=audio_data,
                duration=float(response.headers.get("X-Audio-Duration", 0)),
                format=response.headers.get("Content-Type", "audio/wav").split("/")[-1],
            )

    async def voices(self, model: Optional[str] = None) -> list[VoicesResponse]:
        if not self.session:
            raise TypecastError("Client session not initialized. Use async with.")
        endpoint = "/v1/voices"
        params = {}
        if model:
            params["model"] = model

        async with self.session.get(
            f"{self.host}{endpoint}", params=params
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                self._handle_error(response.status, error_text)

            data = await response.json()
            return [VoicesResponse.model_validate(item) for item in data]

    async def get_voice(self, voice_id: str) -> VoicesResponse:
        if not self.session:
            raise TypecastError("Client session not initialized. Use async with.")
        endpoint = f"/v1/voices/{voice_id}"

        async with self.session.get(f"{self.host}{endpoint}") as response:
            if response.status != 200:
                error_text = await response.text()
                self._handle_error(response.status, error_text)

            data = await response.json()
            # API returns a list, so we take the first element
            if isinstance(data, list) and len(data) > 0:
                return VoicesResponse.model_validate(data[0])
            return VoicesResponse.model_validate(data)
