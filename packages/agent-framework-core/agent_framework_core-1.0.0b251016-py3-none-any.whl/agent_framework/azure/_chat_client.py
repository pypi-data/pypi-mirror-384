# Copyright (c) Microsoft. All rights reserved.

import json
import logging
import sys
from collections.abc import Mapping
from typing import Any, TypeVar

from azure.core.credentials import TokenCredential
from openai.lib.azure import AsyncAzureADTokenProvider, AsyncAzureOpenAI
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from pydantic import ValidationError

from agent_framework import (
    ChatResponse,
    ChatResponseUpdate,
    CitationAnnotation,
    TextContent,
    use_chat_middleware,
    use_function_invocation,
)
from agent_framework.exceptions import ServiceInitializationError
from agent_framework.observability import use_observability
from agent_framework.openai._chat_client import OpenAIBaseChatClient

from ._shared import (
    AzureOpenAIConfigMixin,
    AzureOpenAISettings,
)

if sys.version_info >= (3, 12):
    from typing import override  # type: ignore # pragma: no cover
else:
    from typing_extensions import override  # type: ignore[import] # pragma: no cover

logger: logging.Logger = logging.getLogger(__name__)

TChatResponse = TypeVar("TChatResponse", ChatResponse, ChatResponseUpdate)
TAzureOpenAIChatClient = TypeVar("TAzureOpenAIChatClient", bound="AzureOpenAIChatClient")


@use_function_invocation
@use_observability
@use_chat_middleware
class AzureOpenAIChatClient(AzureOpenAIConfigMixin, OpenAIBaseChatClient):
    """Azure OpenAI Chat completion class."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        deployment_name: str | None = None,
        endpoint: str | None = None,
        base_url: str | None = None,
        api_version: str | None = None,
        ad_token: str | None = None,
        ad_token_provider: AsyncAzureADTokenProvider | None = None,
        token_endpoint: str | None = None,
        credential: TokenCredential | None = None,
        default_headers: Mapping[str, str] | None = None,
        async_client: AsyncAzureOpenAI | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        instruction_role: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize an Azure OpenAI Chat completion client.

        Keyword Args:
            api_key: The API key. If provided, will override the value in the env vars or .env file.
                Can also be set via environment variable AZURE_OPENAI_API_KEY.
            deployment_name: The deployment name. If provided, will override the value
                (chat_deployment_name) in the env vars or .env file.
                Can also be set via environment variable AZURE_OPENAI_CHAT_DEPLOYMENT_NAME.
            endpoint: The deployment endpoint. If provided will override the value
                in the env vars or .env file.
                Can also be set via environment variable AZURE_OPENAI_ENDPOINT.
            base_url: The deployment base URL. If provided will override the value
                in the env vars or .env file.
                Can also be set via environment variable AZURE_OPENAI_BASE_URL.
            api_version: The deployment API version. If provided will override the value
                in the env vars or .env file.
                Can also be set via environment variable AZURE_OPENAI_API_VERSION.
            ad_token: The Azure Active Directory token.
            ad_token_provider: The Azure Active Directory token provider.
            token_endpoint: The token endpoint to request an Azure token.
                Can also be set via environment variable AZURE_OPENAI_TOKEN_ENDPOINT.
            credential: The Azure credential for authentication.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests.
            async_client: An existing client to use.
            env_file_path: Use the environment settings file as a fallback to using env vars.
            env_file_encoding: The encoding of the environment settings file, defaults to 'utf-8'.
            instruction_role: The role to use for 'instruction' messages, for example, summarization
                prompts could use `developer` or `system`.
            kwargs: Other keyword parameters.

        Examples:
            .. code-block:: python

                from agent_framework.azure import AzureOpenAIChatClient

                # Using environment variables
                # Set AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
                # Set AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4
                # Set AZURE_OPENAI_API_KEY=your-key
                client = AzureOpenAIChatClient()

                # Or passing parameters directly
                client = AzureOpenAIChatClient(
                    endpoint="https://your-endpoint.openai.azure.com", deployment_name="gpt-4", api_key="your-key"
                )

                # Or loading from a .env file
                client = AzureOpenAIChatClient(env_file_path="path/to/.env")
        """
        try:
            # Filter out any None values from the arguments
            azure_openai_settings = AzureOpenAISettings(
                # pydantic settings will see if there is a value, if not, will try the env var or .env file
                api_key=api_key,  # type: ignore
                base_url=base_url,  # type: ignore
                endpoint=endpoint,  # type: ignore
                chat_deployment_name=deployment_name,
                api_version=api_version,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
                token_endpoint=token_endpoint,
            )
        except ValidationError as exc:
            raise ServiceInitializationError(f"Failed to validate settings: {exc}") from exc

        if not azure_openai_settings.chat_deployment_name:
            raise ServiceInitializationError(
                "Azure OpenAI deployment name is required. Set via 'deployment_name' parameter "
                "or 'AZURE_OPENAI_CHAT_DEPLOYMENT_NAME' environment variable."
            )

        super().__init__(
            deployment_name=azure_openai_settings.chat_deployment_name,
            endpoint=azure_openai_settings.endpoint,
            base_url=azure_openai_settings.base_url,
            api_version=azure_openai_settings.api_version,  # type: ignore
            api_key=azure_openai_settings.api_key.get_secret_value() if azure_openai_settings.api_key else None,
            ad_token=ad_token,
            ad_token_provider=ad_token_provider,
            token_endpoint=azure_openai_settings.token_endpoint,
            credential=credential,
            default_headers=default_headers,
            client=async_client,
            instruction_role=instruction_role,
            **kwargs,
        )

    @override
    def _parse_text_from_choice(self, choice: Choice | ChunkChoice) -> TextContent | None:
        """Parse the choice into a TextContent object.

        Overwritten from OpenAIBaseChatClient to deal with Azure On Your Data function.
        For docs see:
        https://learn.microsoft.com/en-us/azure/ai-foundry/openai/references/on-your-data?tabs=python#context
        """
        message = choice.message if isinstance(choice, Choice) else choice.delta
        if hasattr(message, "refusal") and message.refusal:
            return TextContent(text=message.refusal, raw_representation=choice)
        if not message.content:
            return None
        text_content = TextContent(text=message.content, raw_representation=choice)
        if not message.model_extra or "context" not in message.model_extra:
            return text_content

        context: dict[str, Any] | str = message.context  # type: ignore[assignment, union-attr]
        if isinstance(context, str):
            try:
                context = json.loads(context)
            except json.JSONDecodeError:
                logger.warning("Context is not a valid JSON string, ignoring context.")
                return text_content
        if not isinstance(context, dict):
            logger.warning("Context is not a valid dictionary, ignoring context.")
            return text_content
        # `all_retrieved_documents` is currently not used, but can be retrieved
        # through the raw_representation in the text content.
        if intent := context.get("intent"):
            text_content.additional_properties = {"intent": intent}
        if citations := context.get("citations"):
            text_content.annotations = []
            for citation in citations:
                text_content.annotations.append(
                    CitationAnnotation(
                        title=citation.get("title", ""),
                        url=citation.get("url", ""),
                        snippet=citation.get("content", ""),
                        file_id=citation.get("filepath", ""),
                        tool_name="Azure-on-your-Data",
                        additional_properties={"chunk_id": citation.get("chunk_id", "")},
                        raw_representation=citation,
                    )
                )
        return text_content
