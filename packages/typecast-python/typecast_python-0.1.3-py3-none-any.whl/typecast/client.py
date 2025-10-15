from typing import Optional

import requests

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


class Typecast:
    """Typecast API Client"""

    def __init__(self, host: Optional[str] = None, api_key: Optional[str] = None):
        self.host = conf.get_host(host)
        self.api_key = conf.get_api_key(api_key)
        self.session = requests.Session()
        self.session.headers.update(
            {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        )

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

    def text_to_speech(self, request: TTSRequest) -> TTSResponse:
        endpoint = "/v1/text-to-speech"
        response = self.session.post(
            f"{self.host}{endpoint}", json=request.model_dump(exclude_none=True)
        )
        if response.status_code != 200:
            self._handle_error(response.status_code, response.text)

        return TTSResponse(
            audio_data=response.content,
            duration=response.headers.get("X-Audio-Duration", 0),
            format=response.headers.get("Content-Type", "audio/wav").split("/")[-1],
        )

    def voices(self, model: Optional[str] = None) -> list[VoicesResponse]:
        endpoint = "/v1/voices"
        params = {}
        if model:
            params["model"] = model

        response = self.session.get(f"{self.host}{endpoint}", params=params)

        if response.status_code != 200:
            self._handle_error(response.status_code, response.text)

        return [VoicesResponse.model_validate(item) for item in response.json()]

    def get_voice(self, voice_id: str) -> VoicesResponse:
        endpoint = f"/v1/voices/{voice_id}"
        response = self.session.get(f"{self.host}{endpoint}")

        if response.status_code != 200:
            self._handle_error(response.status_code, response.text)

        data = response.json()
        # API returns a list, so we take the first element
        if isinstance(data, list) and len(data) > 0:
            return VoicesResponse.model_validate(data[0])
        return VoicesResponse.model_validate(data)
