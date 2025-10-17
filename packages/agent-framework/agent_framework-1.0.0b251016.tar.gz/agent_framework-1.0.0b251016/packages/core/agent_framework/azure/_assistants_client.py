# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, ClassVar

from openai.lib.azure import AsyncAzureADTokenProvider, AsyncAzureOpenAI
from pydantic import ValidationError

from ..exceptions import ServiceInitializationError
from ..openai import OpenAIAssistantsClient
from ._shared import AzureOpenAISettings

if TYPE_CHECKING:
    from azure.core.credentials import TokenCredential

__all__ = ["AzureOpenAIAssistantsClient"]


class AzureOpenAIAssistantsClient(OpenAIAssistantsClient):
    """Azure OpenAI Assistants client."""

    DEFAULT_AZURE_API_VERSION: ClassVar[str] = "2024-05-01-preview"

    def __init__(
        self,
        *,
        deployment_name: str | None = None,
        assistant_id: str | None = None,
        assistant_name: str | None = None,
        thread_id: str | None = None,
        api_key: str | None = None,
        endpoint: str | None = None,
        base_url: str | None = None,
        api_version: str | None = None,
        ad_token: str | None = None,
        ad_token_provider: AsyncAzureADTokenProvider | None = None,
        token_endpoint: str | None = None,
        credential: "TokenCredential | None" = None,
        default_headers: Mapping[str, str] | None = None,
        async_client: AsyncAzureOpenAI | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize an Azure OpenAI Assistants client.

        Keyword Args:
            deployment_name: The Azure OpenAI deployment name for the model to use.
                Can also be set via environment variable AZURE_OPENAI_CHAT_DEPLOYMENT_NAME.
            assistant_id: The ID of an Azure OpenAI assistant to use.
                If not provided, a new assistant will be created (and deleted after the request).
            assistant_name: The name to use when creating new assistants.
            thread_id: Default thread ID to use for conversations. Can be overridden by
                conversation_id property when making a request.
                If not provided, a new thread will be created (and deleted after the request).
            api_key: The API key to use. If provided will override the env vars or .env file value.
                Can also be set via environment variable AZURE_OPENAI_API_KEY.
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
            credential: The Azure credential to use for authentication.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests.
            async_client: An existing client to use.
            env_file_path: Use the environment settings file as a fallback
                to environment variables.
            env_file_encoding: The encoding of the environment settings file.

        Examples:
            .. code-block:: python

                from agent_framework.azure import AzureOpenAIAssistantsClient

                # Using environment variables
                # Set AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
                # Set AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4
                # Set AZURE_OPENAI_API_KEY=your-key
                client = AzureOpenAIAssistantsClient()

                # Or passing parameters directly
                client = AzureOpenAIAssistantsClient(
                    endpoint="https://your-endpoint.openai.azure.com", deployment_name="gpt-4", api_key="your-key"
                )

                # Or loading from a .env file
                client = AzureOpenAIAssistantsClient(env_file_path="path/to/.env")
        """
        try:
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
                default_api_version=self.DEFAULT_AZURE_API_VERSION,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Azure OpenAI settings.", ex) from ex

        if not azure_openai_settings.chat_deployment_name:
            raise ServiceInitializationError(
                "Azure OpenAI deployment name is required. Set via 'deployment_name' parameter "
                "or 'AZURE_OPENAI_CHAT_DEPLOYMENT_NAME' environment variable."
            )

        # Handle authentication: try API key first, then AD token, then Entra ID
        if (
            not async_client
            and not azure_openai_settings.api_key
            and not ad_token
            and not ad_token_provider
            and azure_openai_settings.token_endpoint
            and credential
        ):
            ad_token = azure_openai_settings.get_azure_auth_token(credential)

        if not async_client and not azure_openai_settings.api_key and not ad_token and not ad_token_provider:
            raise ServiceInitializationError("The Azure OpenAI API key, ad_token, or ad_token_provider is required.")

        # Create Azure client if not provided
        if not async_client:
            client_params: dict[str, Any] = {
                "api_version": azure_openai_settings.api_version,
                "default_headers": default_headers,
            }

            if azure_openai_settings.api_key:
                client_params["api_key"] = azure_openai_settings.api_key.get_secret_value()
            elif ad_token:
                client_params["azure_ad_token"] = ad_token
            elif ad_token_provider:
                client_params["azure_ad_token_provider"] = ad_token_provider

            if azure_openai_settings.base_url:
                client_params["base_url"] = str(azure_openai_settings.base_url)
            elif azure_openai_settings.endpoint:
                client_params["azure_endpoint"] = str(azure_openai_settings.endpoint)

            async_client = AsyncAzureOpenAI(**client_params)

        super().__init__(
            model_id=azure_openai_settings.chat_deployment_name,
            assistant_id=assistant_id,
            assistant_name=assistant_name,
            thread_id=thread_id,
            async_client=async_client,  # type: ignore[reportArgumentType]
            default_headers=default_headers,
        )
