# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Module for formatting prompts for different tasks and models."""
from abc import ABC, abstractmethod
from typing import Dict, List, Union

from llm.optimized.inference.constants import TaskType
from llm.optimized.inference.conversation import Conversation


class AbstractPromptFormatter(ABC):
    """Abstract base class for prompt formatters."""

    @abstractmethod
    def format_prompt(
        self,
        task_type: TaskType,
        query: Union[str, Conversation],
        params: Dict,
    ) -> str:
        """Format the prompt based on the task type, query and parameters."""
        raise NotImplementedError("format_prompt method not implemented.")


class Llama2Formatter(AbstractPromptFormatter):
    """Prompt formatter for Llama2 models."""

    def format_prompt(
        self,
        task_type: TaskType,
        query: Union[str, Conversation],
        params: Dict,
    ) -> str:
        """Format the prompt for Llama2 models. Currently a placeholder."""
        if task_type == TaskType.QnA:
            return list(query)
        return str(query)


class Text2ImgFormatter(AbstractPromptFormatter):
    """Prompt formatter for stable diffusion text2img models."""

    def format_prompt(
        self,
        task_type: TaskType,
        query: List[tuple[str, Union[str, None]]],
        params: Dict,
    ) -> str:
        """Format the prompt for text 2 image models. Currently a placeholder."""
        return query
