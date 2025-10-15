# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Module for diffusion model configuration."""


import os
import torch
from typing import Dict, List

try:
    from mii.config import ModelConfig
    from mii.legacy.models.utils import ImageResponse
except ImportError:
    print("MII installation skipped for unit testing.")

from llm.optimized.inference.prompt_formatter import Text2ImgFormatter, AbstractPromptFormatter

from llm.optimized.inference.custom_model_configurations.base_configuration_builder import ModelConfigurationBuilder
from llm.optimized.inference.constants import EngineName, TaskType
from llm.optimized.inference.custom_model_configurations.schema_output import (
    ImageTaskInferenceResult,
    TextToImageSchema,
)
from llm.optimized.inference.logging_config import configure_logger
from llm.optimized.inference.utils import convert_image_to_bytes, get_gpu_device_capability

logger = configure_logger(__name__)


class DiffusionConfigurationBuilder(ModelConfigurationBuilder):
    """Diffusion model configuration builder for optimization inference configuration."""

    MLFLOW_MODEL_PATH = "mlflow_model_folder/artifacts/INPUT_model_path"

    def __init__(self, task) -> None:
        """Initialize the DiffusionConfiguration with the diffusion supported task.

        :param task: task supported by diffusion and optimization engine
        :type task: TaskType
        """
        self._task = task
        if os.environ.get("NUM_REPLICAS") is None:
            # Set number of replicas equal to number of gpus.
            os.environ["NUM_REPLICAS"] = str(torch.cuda.device_count())

    @property
    def tensor_parallel(self) -> int:
        """Get tensor parallel. Set default tensor parallel, if not set by user."""
        if os.environ.get("TENSOR_PARALLEL") is None:
            os.environ["TENSOR_PARALLEL"] = "1"
        return int(os.environ["TENSOR_PARALLEL"])

    @property
    def engine(self) -> EngineName:
        """Diffusion supported optimization engine.

        :return: Optimization engine to use.
        :rtype: EngineName enum
        """
        return EngineName.MII_V1

    def get_task_config(self) -> Dict[str, str]:
        """Task config for diffusion model.

        :return: task configuration
        :rtype: Dict[str, str]
        """
        return {"task_type": self._task}

    def get_optimization_config(self) -> Dict[str, str]:
        """Optimization config for diffusion model.

        :return: optimization configuration
        :rtype: Dict[str, str]
        """
        default_deployment_name = f"{self._task}-deployment"[:30]
        return {
            "deployment_name": os.getenv("DEPLOYMENT_NAME", default_deployment_name),
            "mii_configs": {},
        }

    @staticmethod
    def _post_processing_text_to_image(
        responses: "ImageResponse", inference_time: float, prompts: List[str] = None, num_images_per_prompt: int = 1
    ) -> List[ImageTaskInferenceResult]:
        """Post processing for text to image task.

        :param responses: response from mii server
        :type responses: ImageResponse
        :param inference_time: inference time in milliseconds
        :type inference_time: float
        :param prompts: input prompts, defaults to None
        :type prompts: List[str], optional
        :param num_images_per_prompt: number of images per prompt, defaults to 1
        :type num_images_per_prompt: int, optional
        :return: Image Task prediction output
        :rtype: List[ImageTaskInferenceResult]
        """
        result = []
        images = responses.images
        nsfw_content_detected = responses.nsfw_content_detected
        for i in range(len(images)):
            result.append(
                ImageTaskInferenceResult(
                    response=TextToImageSchema(
                        generated_image=images[i],
                        prompt=prompts[i // num_images_per_prompt][0] if prompts else None,
                        nsfw_content_detected=nsfw_content_detected[i] if nsfw_content_detected else None,
                    ),
                    inference_time_ms=inference_time,
                )
            )
        return result

    def post_processing(self, responses: any, inference_time: float, **kwargs) -> List[ImageTaskInferenceResult]:
        """Process diffusion model output to generate the final response.

        :param responses: model responses
        :type responses: any
        :param inference_time: inference time in milliseconds
        :type inference_time: float
        :param kwargs: additional arguments
        :type kwargs: Dict
        :return: processed model response
        :rtype: List of ImageTaskInferenceResult
        """
        TASK_POST_PROCESSING_MAP = {TaskType.TEXT_TO_IMAGE: self._post_processing_text_to_image,
                                    TaskType.TEXT_TO_IMAGE_INPAINTING: self._post_processing_text_to_image
                                    }
        prompts = kwargs.get("prompts")
        num_images_per_prompt = kwargs.get("num_images_per_prompt", 1)
        result = TASK_POST_PROCESSING_MAP[self._task](responses, inference_time, prompts, num_images_per_prompt)
        return result

    def update_mii_model_config(self, model_config: "ModelConfig") -> None:
        """Override the default MII model configuration depending on task and GPU compute capability.

        :param model_config: MII model configuration
        :type model_config: ModelConfig
        """
        # Triton kernel supported on only 7.0+ GPUs. V100 is 7.0
        model_config.load_with_sys_mem = False  # Not supported for diffusers
        model_config.task = self._task
        model_config.model_path = self.MLFLOW_MODEL_PATH
        if get_gpu_device_capability() <= 7.0:
            model_config.replace_with_kernel_inject = False
            model_config.meta_tensor = True
            model_config.enable_cuda_graph = True

    def get_formatter(self) -> AbstractPromptFormatter:
        """Return formatter object for specific tasks supported by diffusion model."""
        TASK_FORMATTER_MAP = {
            TaskType.TEXT_TO_IMAGE: Text2ImgFormatter,
            TaskType.TEXT_TO_IMAGE_INPAINTING: Text2ImgFormatter
        }
        return TASK_FORMATTER_MAP[self._task]()

    def pre_processing(self, queries: Dict, **kwargs) -> None:
        """Preprocess the input queries for the model.

        :param queries: input queries
        :type queries: Dict
        :param kwargs: additional arguments
        :type kwargs: Dict
        """
        TASK_PRE_PROCESSING_MAP = {TaskType.TEXT_TO_IMAGE: self._pre_processing_text_to_image,
                                   TaskType.TEXT_TO_IMAGE_INPAINTING: self._pre_processing_text_to_image_inpainting
                                   }
        TASK_PRE_PROCESSING_MAP[self._task](queries)

    def _pre_processing_text_to_image_inpainting(self, queries: Dict) -> None:
        """Preprocess the input queries for inpainting task.

        :param queries: input queries
        :type queries: Dict
        :param kwargs: additional arguments
        :type kwargs: Dict
        """
        input_dict = queries.pop("query")

        prompt = []
        negative_prompt = []
        image = []
        mask_image = []
        for i in range(len(input_dict)):
            prompt.append(input_dict[i][0])
            if len(input_dict[i]) > 1:
                negative_prompt.append(input_dict[i][1])
            else:
                negative_prompt.append("")
            image.append(convert_image_to_bytes(input_dict[i][2]))
            mask_image.append(convert_image_to_bytes(input_dict[i][3]))
        queries["prompt"] = prompt
        queries["negative_prompt"] = negative_prompt
        queries["image"] = image
        queries["mask_image"] = mask_image

    def _pre_processing_text_to_image(self, queries: Dict, **kwargs) -> None:
        """Preprocess the input queries for the text to image task.

        :param queries: input queries
        :type queries: Dict
        :param kwargs: additional arguments
        :type kwargs: Dict
        """
        input_dict = queries.pop("query")

        prompt = []
        negative_prompt = []
        for i in range(len(input_dict)):
            prompt.append(input_dict[i][0])
            if len(input_dict[i]) > 1:
                negative_prompt.append(input_dict[i][1])
            else:
                negative_prompt.append("")
        queries["prompt"] = prompt
        queries["negative_prompt"] = negative_prompt
