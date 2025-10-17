from __future__ import annotations

from abc import ABC, abstractmethod
import json
from typing import TYPE_CHECKING, Any

from httpx import AsyncClient, Headers, Response
from pydantic import BaseModel, Field, ValidationError, computed_field

from bear_dereth.constants import HTTPStatusCode
from bear_dereth.exceptions import UnexpectedStatusCodeError
from bear_dereth.models.type_fields import TokenModel

if TYPE_CHECKING:
    from bear_utils.ai._config import AIEndpointConfig, AISetup


class BaseResponseParser[T_Response: BaseModel](ABC):
    """Base parser using Pydantic models for type-safe parsing."""

    def __init__(self, response_model: type[T_Response]) -> None:
        self.response_model: type[T_Response] = response_model

    @abstractmethod
    async def parse(self, raw_response: dict[str, Any], data_key: str = "output") -> T_Response:
        """Parse response using Pydantic model validation."""

    def get_default_response(self) -> T_Response:
        """Create default response using Pydantic model."""
        return self.response_model()


class BaseModelParser[T_Response: BaseModel](BaseResponseParser[T_Response]):
    """Parser for JSON responses with flexible output structure."""

    def __init__(self, response_model: type[T_Response]):
        super().__init__(response_model=response_model)
        self.model: type[T_Response] = response_model

    async def parse(self, raw_response: dict[str, Any], data_key: str = "output") -> T_Response:
        """Parse JSON response with configurable validation and transformation."""
        output: dict[str, Any] = raw_response.get(data_key, {})
        try:
            response_data: dict[str, Any] = json.loads(output) if isinstance(output, str) else output
            return self.response_model.model_validate(response_data)
        except (json.JSONDecodeError, ValidationError):
            return self.get_default_response()


class BaseEndpoint[T_Response: BaseModel](ABC):
    """A base abstract class for AI endpoints."""

    def __init__(self, config: AIEndpointConfig, response_parser: BaseResponseParser[T_Response]) -> None:
        self.config: AIEndpointConfig = config
        self.ai: AISetup = config.ai
        self.response_parser: BaseResponseParser[T_Response] = response_parser
        self.session_id: str | None = None
        self.headers = StandardHeaders(token=self.ai.token)

    @abstractmethod
    async def send_message(self, message: str, session_id: str) -> Any:
        """Send a message to the AI endpoint."""

    async def _post(self, client: AsyncClient, json: ToServerJson) -> Response:
        res: Response = await client.post(
            url=self.config.url,
            json=json.model_dump(),
            headers=Headers(self.headers.model_dump()),
        )
        if res.status_code != HTTPStatusCode.SERVER_OK:
            raise UnexpectedStatusCodeError(res.status_code)
        return res


class StandardHeaders(BaseModel):
    """Standard headers for AI requests."""

    model_config = {"validate_by_name": True, "serialize_by_alias": True}

    content_type: str = Field(default="application/json", alias="Content-Type")
    token: TokenModel = Field(default_factory=TokenModel, description="Authorization token if required", exclude=True)

    @computed_field(alias="Authorization", repr=False)
    def authorization(self) -> str:
        return f"Bearer {self.token.get_secret_value()}"


class ToServerJson(BaseModel):
    """Standard JSON payload for AI requests."""

    model_config = {"serialize_by_alias": True}

    chat_model: str = Field(default="", serialization_alias="chatModel", description="The chat model to use")
    chat_input: str = Field(default="", serialization_alias="chatInput", description="The user message")
    session_id: str = Field(default="", serialization_alias="sessionId", description="The session identifier")
    sys_prompt: str | None = Field(default=None, serialization_alias="systemPrompt")
