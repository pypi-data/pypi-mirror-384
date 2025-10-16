import logging

import litellm

from .._litellm_wrapper import LiteLLMWrapper

# litellm.drop_params=True
from .._model_exception_base import FunctionCallingNotSupportedError, ModelError
from ..providers import ModelProvider

LOGGER_NAME = "AZURE_AI"
logger = logging.getLogger(__name__)


class AzureAIError(ModelError):
    pass


class AzureAILLM(LiteLLMWrapper):
    @classmethod
    def model_type(cls):
        return ModelProvider.AZUREAI

    def __init__(
        self,
        model_name: str,
        **kwargs,
    ):
        """Initialize an Azure AI LLM instance.

        Args:
            model_name (str): Name of the Azure AI model to use.
            **kwargs: Additional arguments passed to the parent LiteLLMWrapper.

        Raises:
            AzureAIError: If the specified model is not available or if there are issues with the Azure AI service.
        """
        super().__init__(model_name, **kwargs)

        # Currently matching names to Azure models is case sensitive
        self._available_models = [model.lower() for model in litellm.azure_ai_models]
        self._is_model_available()

        self.logger = logger

    def chat(self, messages, **kwargs):
        try:
            return super().chat(messages, **kwargs)
        except litellm.InternalServerError as e:
            raise AzureAIError(
                reason=f"Azure AI LLM error while processing the request: {e}"
            ) from e

    def chat_with_tools(self, messages, tools, **kwargs):
        if not litellm.supports_function_calling(model=self._model_name.lower()):
            raise FunctionCallingNotSupportedError(self._model_name)

        try:
            return super().chat_with_tools(messages, tools, **kwargs)
        except litellm.InternalServerError as e:
            raise AzureAIError(
                reason=f"Azure AI LLM error while processing the request: {e}"
            ) from e

    def _is_model_available(self) -> None:
        """Check if the model is available and supports tool calling."""
        if self._model_name.lower() not in self._available_models:
            raise AzureAIError(
                reason=(
                    f"Model '{self._model_name}' is not available. "
                    f"Available models: {self._available_models}"
                )
            )

    def _tool_calling_supported(self) -> bool:
        """Check if the model supports tool calling."""
        tool_calling_supported = [
            (model, litellm.supports_function_calling(model=model))
            for model in self._available_models
        ]
        return tool_calling_supported
