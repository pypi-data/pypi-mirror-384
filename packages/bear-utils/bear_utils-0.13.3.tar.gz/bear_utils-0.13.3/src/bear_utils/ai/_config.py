from typing import Annotated

from pydantic import AnyHttpUrl, BaseModel, BeforeValidator, ConfigDict
from rich.markdown import Markdown

from bear_dereth.config.config_manager import ConfigManager
from bear_dereth.models.type_fields import TokenModel
from bear_utils.ai._common import AIModel, AIPlatform, EnvironmentMode as EnvMode

VerifyMarkdown = Annotated[Markdown, BeforeValidator(Markdown)]

DEFAULT_TIMEOUT = 20


class AISetup(BaseModel):
    """Basic setup for AI communication."""

    url: AnyHttpUrl = AnyHttpUrl("https://example.com")
    model: AIModel | str = AIModel.GPT_4_1_NANO
    platform: AIPlatform = AIPlatform.OPENAI
    token: TokenModel = TokenModel()


class AIEndpointConfig[T_Response: BaseModel](BaseModel):
    """Configuration for AI endpoint communication."""

    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    name: str = ""
    timeout: int = DEFAULT_TIMEOUT
    response_type: T_Response | None = None
    system_prompt: str | None = None
    env: EnvMode = EnvMode.PROD
    ai: AISetup = AISetup()

    @property
    def url(self) -> str:
        """Get the URL based on the environment."""
        return str(self.ai.url)


if __name__ == "__main__":
    config_manager = ConfigManager(AIEndpointConfig, program_name="bear_utils")
    config = config_manager.config

    print(config.model_dump_json(exclude_none=True, indent=4))
