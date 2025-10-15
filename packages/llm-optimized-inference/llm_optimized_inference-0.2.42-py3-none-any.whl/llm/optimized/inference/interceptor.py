import os
from typing import Optional
from abc import ABC
from llm.optimized.inference.api_server_setup.protocol import ContentPartType
from llm.optimized.inference.constants import ModelTypes
from llm.optimized.inference.logging_config import configure_logger

logger = configure_logger(__name__)


class PhiOLoraModel:
    """Lora model names for Phio model type."""

    PHIO_VISION_LORA = "phio-vision-lora"
    PHIO_SPEECH_LORA = "phio-speech-lora"


class BaseRequestInterceptor:
    """Base vLLM request interceptor."""

    def modify_request(self, request):
        """Modify chat completion request."""
        return request


class PhiOChatRequestInterceptor(BaseRequestInterceptor):
    """PhiO vLLM request interceptor."""

    def modify_request(self, request):
        """Modify chat completion request."""
        model_name = self._get_model_name_for_lora(prompts=request.messages)
        if model_name:
            request.model = model_name
        return request

    def _get_model_name_for_lora(self, prompts):
        images: bool = False
        audios: bool = False
        texts: bool = False
        model_name = None

        messages = list(prompts)
        logger.info(f"Request prompt is {messages}")
        for message in messages:
            content = message["content"]
            if isinstance(content, list):
                for item in content:
                    item_type = item.get("type")
                    if item_type == ContentPartType.text.value:
                        texts = True
                    elif (item_type == ContentPartType.image_url.value
                          or item_type == ContentPartType.image.value):
                        images = True
                    elif (item_type == ContentPartType.audio_url.value
                          or item_type == ContentPartType._input_audio.value):
                        audios = True

        if texts and images and audios:
            model_name = None
        elif images and audios:
            model_name = PhiOLoraModel.PHIO_VISION_LORA
        elif images:
            model_name = PhiOLoraModel.PHIO_VISION_LORA
        elif audios:
            model_name = PhiOLoraModel.PHIO_SPEECH_LORA

        logger.info(f"LoRA model name for Phio {model_name}")
        return model_name


class InterceptorFactory(ABC):
    """Factory to fetch request interceptor."""

    _interceptor: Optional[BaseRequestInterceptor] = None

    @staticmethod
    def get_interceptor() -> BaseRequestInterceptor:
        """Return request interceptor."""
        inference_model_type = os.getenv("INFERENCE_MODEL_TYPE", None)

        if InterceptorFactory._interceptor is None:
            if ModelTypes.PHIO == inference_model_type:
                InterceptorFactory._interceptor = PhiOChatRequestInterceptor()
            else:
                InterceptorFactory._interceptor = BaseRequestInterceptor()

            logger.info(
                f"Instance generated is {InterceptorFactory._interceptor}")
        return InterceptorFactory._interceptor
