# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""This module provides the MIRPayload class that codifies the payload that is received in the scoring script."""
import json
import os
from dataclasses import dataclass
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union

from llm.optimized.inference.configs import SerializableDataClass
from llm.optimized.inference.constants import TaskType, ModelTypes
from llm.optimized.inference.logging_config import configure_logger
from llm.optimized.inference.conversation import TextMessage, MultimodalMessage
from transformers import AutoTokenizer

logger = configure_logger(__name__)

DEFAULT_TOKENIZER_PATH = "mlflow_model_folder/components/tokenizer"
DEFAULT_MODEL_PATH = "mlflow_model_folder/data/model"
MODEL_ARTIFACT_PATH = "model_artifact/model"


@dataclass
class MIRPayload(SerializableDataClass):
    """Json serializable dataclass that represents the input received from the server."""

    query: Union[List[TextMessage], List[MultimodalMessage], str, List[str], List[Tuple[str, str]]]
    params: Dict[str, Any]
    task_type: str
    is_preview_format: bool

    @classmethod
    def from_dict(cls, mir_input_data: Dict, model_config: Optional[Dict] = None):
        """Create an instance of MIRPayload from input data received from the server."""
        query, params, task_type, is_preview_format = get_request_data(mir_input_data, model_config)
        return MIRPayload(query, params, task_type, is_preview_format)

    def convert_query_to_list(self) -> None:
        """Convert the query parameter into a list.

        FMScore.run expects a list of prompts. In the case of chat completion, a single string
        is produced and needs to be put inside of a list.
        """
        if not isinstance(self.query, list):
            self.query = [self.query]

    def update_params(self, new_params: Dict) -> None:
        """Update current parameters to the new parameters the MIRPayload should have."""
        self.params = new_params


def get_processed_input_data_for_chat_completion(
    dialog: List[Dict[str, Any]],
    add_generation_prompt: bool, model_config: Optional[Dict] = None
) -> str:
    r"""Process chat completion input request.

    example input:
    [
        {
            "role": "user",
            "content": "What is the tallest building in the world?"
        },
        {
            "role": "assistant",
            "content": "As of 2021, the Burj Khalifa in Dubai"
        },
        {
            "role": "user",
            "content": "and in Africa?"
        },
    ]
    example output:
    "[INST]What is the tallest building in the world?[/INST]
    As of 2021, the Burj Khalifa in Dubai\n
    [INST]and in Africa?[/INST]"
    """
    # if model type is phi3-v, just return the json string of the dialog
    print("Dialog: ", dialog)
    if model_config is not None and model_config.get("model_type", "") in (
        ModelTypes.PHI3_V,
        ModelTypes.LLAMA_VISION_TEXT,
        ModelTypes.PHIO
    ):
        return json.dumps(dialog)

    # get path to model folder
    tokenizer_path = str(os.path.join(os.getenv("AZUREML_MODEL_DIR", ""), DEFAULT_TOKENIZER_PATH))

    if not os.path.exists(tokenizer_path):
        tokenizer_path = os.path.join(
            os.getenv("AZUREML_MODEL_DIR", ""),
            DEFAULT_MODEL_PATH,
        )

    if not os.path.exists(tokenizer_path):
        tokenizer_path = os.path.join(
            os.getenv("AZUREML_MODEL_DIR", ""),
            MODEL_ARTIFACT_PATH,
        )

    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path,
                                              use_default_system_prompt=False,
                                              trust_remote_code=True)
    # apply template to format chat conversation
    chat_conv = tokenizer.apply_chat_template(dialog, tokenize=False, add_generation_prompt=add_generation_prompt)
    return chat_conv


def process_input_data_for_text_to_image(
    inputs: Dict[str, any]
) -> Tuple[List[Tuple[str, str, str, str]], Dict[str, Any]]:
    """Process text to image task input request to make it suitable for model.

    :param inputs: input data
    :type inputs: Dict[str, any]
    :return: Processed input data in list of tuple (prompt and negative_prompt(optional)) for model and parameters.
    For text-to-image-inpainting task, it will return `init_image` and `mask_image`.
    For text-to-image task these values would be None
    :rtype: Tuple[List[Tuple[str, str]], Dict[str, Any]]
    """
    params = inputs.pop("parameters", {})
    if "columns" in inputs and "data" in inputs:
        input_df = pd.DataFrame(**inputs)
        prompt_data = input_df["prompt"].to_list()
        number_of_prompts = len(prompt_data)

        negative_prompt_data = (
            input_df["negative_prompt"].to_list()
            if "negative_prompt" in input_df.columns
            else [""] * number_of_prompts
        )

        init_image = (
            input_df["image"].to_list()
            if "image" in input_df.columns
            else [None] * number_of_prompts
        )

        mask_image = (
            input_df["mask_image"].to_list()
            if "image" in input_df.columns
            else [None] * number_of_prompts
        )

        input_data = []
        for i in range(number_of_prompts):
            input_data.append([prompt_data[i],
                               "" if pd.isna(negative_prompt_data[i]) else negative_prompt_data[i],
                               init_image[i],
                               mask_image[i]
                               ])
    return input_data, params


def get_request_data(
    data,
    model_config: Optional[Dict] = None
) -> (Tuple)[Union[str, List[str]], Dict[str, Any], str, bool]:
    """Process and validate inference request.

    return type for chat-completion: str, dict, str, bool
    return type for text-generation: list, dict, str, bool
    """
    try:
        is_preview_format = True
        inputs = data.get("input_data", None)
        task_type = data.get("task_type", TaskType.TEXT_GENERATION)
        # TODO: Update this check once all tasks are updated to use new input format
        if task_type != TaskType.TEXT_GENERATION:
            if not isinstance(inputs, dict):
                raise Exception("Invalid input data")

        if task_type == "chat-completion":
            task_type = TaskType.CONVERSATIONAL
        elif task_type in [TaskType.TEXT_TO_IMAGE, TaskType.TEXT_TO_IMAGE_INPAINTING]:
            input_data, params = process_input_data_for_text_to_image(inputs)
            return input_data, params, task_type, is_preview_format

        input_data = []  # type: Union[str, List[str]]
        params = {}  # type: Dict[str, Any]

        # Input format is being updated
        # Original text-gen input: {"input_data": {"input_string": ["<query>"], "parameters": {"k1":"v1", "k2":"v2"}}}
        # New text-gen input: {"input_data": ["<query>"], "params": {"k1":"v1", "k2":"v2"}}
        # For other tasks, new input format is not provided yet, so keeping original format for now.
        if task_type == TaskType.TEXT_GENERATION and "input_string" not in inputs:
            is_preview_format = False
            input_data = inputs
            params = data.get("params", {})
        else:
            input_data = inputs["input_string"]
            params = inputs.get("parameters", {})

        if not isinstance(input_data, list):
            raise Exception("query is not a list")

        if not isinstance(params, dict):
            raise Exception("parameters is not a dict")

        if task_type == TaskType.CONVERSATIONAL:
            logger.info("chat-completion task. Processing input data")
            add_generation_prompt = params.pop("add_generation_prompt", True)
            input_data = get_processed_input_data_for_chat_completion(input_data, add_generation_prompt, model_config)

        return input_data, params, task_type, is_preview_format
    except Exception as e:
        task_type = data.get("task_type", TaskType.TEXT_GENERATION)
        if task_type == "chat-completion":
            correct_input_format = (
                '{"input_data": {"input_string": [{"role":"user", "content": "str1"}, '
                '{"role": "assistant", "content": "str2"} ....], "parameters": {"k1":"v1", "k2":"v2"}}}'
            )
        elif task_type == TaskType.TEXT_TO_IMAGE:
            correct_input_format = (
                '{"input_data": {"columns": ["prompt", "negative_prompt"], \
                "data": [{"prompt": "prompt(str)", "negative_prompt": "negative prompt (optional, str)"}], '
                '"parameters": {"k1":"v1", "k2":"v2"}}}'
            )
        elif task_type == TaskType.TEXT_TO_IMAGE_INPAINTING:
            correct_input_format = (
                '{"input_data": {"columns": ["prompt", "negative_prompt", "image", "mask_image"], \
                "data": [{"prompt": "prompt(str)", "negative_prompt": "negative prompt (optional, str)", \
                "image": "init_image (base64/url)", "mask_image": "mask_image (base64/url)"}], '
                '"parameters": {"k1":"v1", "k2":"v2"}}}'
            )
        else:
            correct_input_format = (
                '{"input_data": ["str1", "str2", ...], '
                '"params": {"k1":"v1", "k2":"v2"}}'
            )

        raise Exception(
            json.dumps(
                {
                    "error": (
                        "Expected input format: \n" + correct_input_format
                    ),
                    "exception": str(e),
                },
            ),
        )
