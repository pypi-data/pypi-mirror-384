# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""This module provides classes and methods for handling inference tasks."""

import os
import socket
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from llm.optimized.inference.constants import ServerSetupParams, TaskType
from llm.optimized.inference.logging_config import configure_logger
from transformers import AutoTokenizer
from llm.optimized.inference.utils import box_logger, log_execution_time

logger = configure_logger(__name__)


@dataclass
class InferenceResult:
    """Data class for storing inference results."""

    response: str
    inference_time_ms: float
    time_per_token_ms: float
    generated_tokens: List[Any]
    prompt_num: int
    error: Optional[str] = None
    scores: Optional[List[Any]] = None
    n_prompt_tokens: Optional[int] = None
    n_completion_tokens: Optional[int] = None

    def print_results(self):
        """Print the inference results of a single prompt."""
        if self.error:
            msg = f"## Inference Results ##\n ERROR: {self.error}"
        else:
            # TODO: record time per prompt in mii so we can show inference time for each prompt
            msg = f""" ## Prompt {self.prompt_num} Results ##\n Total Tokens Generated: {len(self.generated_tokens)}"""
        box_logger(msg)


class BaseEngine(ABC):
    """Base class for inference engines backends."""

    @abstractmethod
    def load_model(self, env=None):
        """Abstract method to load the model."""
        raise NotImplementedError("load_model method not implemented.")

    def init_client(self):
        """Initialize client[s] for the engine to receive requests on."""
        pass

    @property
    def server_url(self) -> str:
        """Return the server url for the engine."""
        return ""

    @abstractmethod
    def generate(self, prompts: List[str], params: Dict, ) -> List[InferenceResult]:
        """Abstract method to generate responses for given prompts."""
        raise NotImplementedError("generate method not implemented.")

    @abstractmethod
    def generate_openai_response(self, request, headers):
        """Abstract method to generate response in open ai alike schema."""
        raise NotImplementedError("generate_openai_response method not implemented")

    def _del_prompt_if_req(
        self,
        prompt: str,
        response: str,
        return_full_text: bool = True,
        force: bool = False,
    ) -> str:
        """Delete the prompt from the response if required."""
        if force:
            return response[len(prompt):]
        elif self.task_config.task_type == TaskType.TEXT_GENERATION:
            if not return_full_text:
                return response[len(prompt):]
            return response
        elif self.task_config.task_type == TaskType.CONVERSATIONAL:
            return response[len(prompt):]
        else:
            raise ValueError(f"Invalid task type {self.task_config.task_type}.")

    # Helper function to check if a port is open
    def is_port_open(self, host: str = "localhost", port: int = 8000, timeout: float = 1.0) -> bool:
        """Check if a port is open on the given host."""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (ConnectionRefusedError, TimeoutError, OSError):
            return False

    @log_execution_time
    def wait_until_server_healthy(self, host: str, port: int, timeout: float = 1.0):
        """Wait until the server is healthy."""
        start_time = time.time()
        while time.time() - start_time < ServerSetupParams.WAIT_TIME_MIN * 60:
            is_healthy = self.is_port_open(host, port, timeout)
            if is_healthy:
                if os.environ.get("LOGGING_WORKER_ID", "") == str(os.getpid()):
                    logger.info("Server is healthy.")
                return
            if os.environ.get("LOGGING_WORKER_ID", "") == str(os.getpid()):
                logger.info("Waiting for server to start...")
            time.sleep(30)
        raise Exception("Server did not become healthy within 15 minutes.")

    @log_execution_time
    def get_tokens(self, response: str):
        """Load tokenizer and get tokens from a prompt."""
        if not hasattr(self, "tokenizer"):
            if getattr(self.engine_config, "tokenizer", None) is not None:
                self.tokenizer = AutoTokenizer.from_pretrained(self.engine_config.tokenizer, trust_remote_code=True)
            else:
                self.tokenizer = AutoTokenizer.from_pretrained(self.engine_config.model_id, trust_remote_code=True)
        tokens = self.tokenizer.encode(response)
        return tokens
