# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Adapter for input request."""
import copy
from fastapi import Request, HTTPException
from llm.optimized.inference.api_server_setup.protocol import ChatCompletionRequest, ChatMessage, \
    ChatRole, ContentPart, ContentPartType
from llm.optimized.inference.constants import ExtraParameters, ModelInfo, SupportedTask, EngineName


def get_adapter(request, raw_request, model_info, engine_config):
    """Get adapter based on loaded model info."""
    if model_info.get(ModelInfo.MODEL_PROVIDER, "") == "mistral" \
       and model_info.get(ModelInfo.MODEL_TYPE, "") == SupportedTask.CHAT_COMPLETION:
        return MixtralChatCompletionAdapter(request, raw_request)

    if model_info.get(ModelInfo.MODEL_TYPE, "") == SupportedTask.CHAT_COMPLETION \
       and engine_config["engine_name"] == EngineName.VLLM:
        return VllmChatCompletionsAdapter(request, raw_request)

    # Default return original request object
    return BaseAdapter(request, raw_request)


class BaseAdapter:
    """Default adapter for input request."""

    def __init__(self, req, raw_req):
        """Initialize the BaseAdapter with the given request."""
        self.req = copy.deepcopy(req)
        self.headers = copy.deepcopy(raw_req.headers)
        self.path = getattr(raw_req.url, "path", "")

    def adapt(self):
        """Return the original request."""
        self.validate()
        return self.req

    def validate(self):
        """Validate input request for all the models."""
        # Skip validation if path is /v1/completions or /v1/chat/completions

        if self.path in ["/v1/completions", "/v1/chat/completions"]:
            return
        extra_params_setting_str = self.headers.get(ExtraParameters.KEY, None)
        if extra_params_setting_str is not None and extra_params_setting_str not in ExtraParameters.OPTIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unexpected EXTRA_PARAMETERS option {extra_params_setting_str}, "
                       f"expected options are {ExtraParameters.OPTIONS}"
            )

        # default to be error
        if (extra_params_setting_str is None or extra_params_setting_str == "error") \
           and self.req.model_extra and len(self.req.model_extra) > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Extra parameters {list(self.req.model_extra.keys())} are not allowed "
                       f"when {ExtraParameters.KEY} is not set or set to be '{ExtraParameters.ERROR}'. "
                       f"Set extra-parameters to '{ExtraParameters.PASS_THROUGH}' to pass to the model."
            )

        self.req._extra_param_setting = extra_params_setting_str


class VllmChatCompletionsAdapter(BaseAdapter):
    """Input request adapter for vllm supported chat models."""

    def __init__(self, req: ChatCompletionRequest, raw_req: Request):
        """Initialize the adapter for vllm supported chat models with the given request."""
        super().__init__(req, raw_req)

    def adapt(self) -> ChatCompletionRequest:
        """Adapt vllm supported chat models."""
        # first validate input request
        self.validate()
        return self.req

    def validate(self):
        """Validate request for vllm supported chat models."""
        super().validate()
        if self.req.tools is not None or self.req.tool_choice is not None:
            raise HTTPException(
                status_code=400,
                detail="Tools and tool_choice are not supported."
            )


class MixtralChatCompletionAdapter(VllmChatCompletionsAdapter):
    """Input request adapter for mixtral chat models."""

    def __init__(self, req: ChatCompletionRequest, raw_req: Request):
        """Initialize the adapter for mixtral chat models with the given request."""
        super().__init__(req, raw_req)

    def adapt(self) -> ChatCompletionRequest:
        """Adapt mixtral chat models."""
        # first validate input request
        self.validate()

        # 2 cases:
        # 1. theres only 1 system message or first 2 messages are [system, assistant],
        #    update the first system message to user
        if self.req.messages[0].role == "system":
            if len(self.req.messages) == 1 or \
               len(self.req.messages) >= 2 and self.req.messages[1].role == "assistant":
                self.req.messages[0].role = "user"
            # 2. first 2 messages are [system, user]
            elif self.req.messages[1].role == "user":
                new_message = ChatMessage(
                    role=ChatRole.user,
                    content=[
                        ContentPart(
                            type=ContentPartType.text,
                            text=self.req.messages[0].content
                        ),
                        ContentPart(
                            type=ContentPartType.text,
                            text=self.req.messages[1].content
                        )
                    ]
                )

                self.req.messages = [new_message] + self.req.messages[2:]

        return self.req

    def validate(self):
        """Validate request for mixtral chat models."""
        super().validate()
        if self.req.response_format is not None and self.req.response_format.type == "json_object":
            raise HTTPException(
                status_code=400,
                detail="mixtral model does not support json response format."
            )
