# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Factory class for getting model configuration object."""


from llm.optimized.inference.custom_model_configurations.base_configuration_builder import ModelConfigurationBuilder
from llm.optimized.inference.constants import TaskType
from llm.optimized.inference.custom_model_configurations.diffusion_configuration_builder import \
    DiffusionConfigurationBuilder


class ModelConfigFactory:
    """Factory class for getting model configuration object."""

    @staticmethod
    def get_config_builder(task: TaskType, **kwargs) -> ModelConfigurationBuilder:
        """Get model configuration object.

        :param task: task supported by the inference optimization engine
        :type task: TaskType
        :param kwargs: keyword arguments (model_type: supported model family for task).
        :type kwargs: dict
        :raises ValueError: Invalid task or model type
        :return: model configuration object
        :rtype: ModelConfiguration
        """
        model_type = kwargs.pop("model_type", "")
        if task in [TaskType.TEXT_TO_IMAGE, TaskType.TEXT_TO_IMAGE_INPAINTING] and model_type == "stable-diffusion":
            return DiffusionConfigurationBuilder(task)
        else:
            raise ValueError("Invalid task or model type.")
