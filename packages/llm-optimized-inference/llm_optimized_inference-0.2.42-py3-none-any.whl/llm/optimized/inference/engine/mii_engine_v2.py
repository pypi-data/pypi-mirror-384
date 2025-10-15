# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Mii Engine module.

This module contains the MiiEngineV2 class which is responsible for initializing the MII server and client,
generating responses for given prompts, and managing the allocation of processes and load balancing.
"""
import json
import os
import time
from typing import Dict, List

import mii
from llm.optimized.inference.configs import EngineConfig, TaskConfig
from llm.optimized.inference.constants import MIIGenerationParams
from llm.optimized.inference.engine.engine import BaseEngine, InferenceResult
from llm.optimized.inference.logging_config import configure_logger
from mii.backend import MIIClient, MIIServer
from llm.optimized.inference.utils import log_execution_time

logger = configure_logger(__name__)


# TODO: Move them to mii config
MAX_TOKENS = int(os.environ.get("MAX_TOTAL_TOKENS", 4096))


class MiiEngineV2(BaseEngine):
    """Inference engine using MII methods."""

    def __init__(self, config: EngineConfig, task_config: TaskConfig):
        """Initialize the MiiEngine with the given engine and task configurations."""
        self.engine_config = config
        self.task_config = task_config
        self.model = None
        self.mii_config = self._get_mii_config()

    def load_model(self, env=None):
        """Initialize MII server and MII client."""
        logger.info("MII Config: " + str(self.mii_config))
        logger.info("Start server setup")
        self.mii_server = MIIServer(self.mii_config)
        logger.info("Completed server setup")

    def init_client(self):
        """Initialize the MII client."""
        # wait until server is healthy then create client
        self.wait_until_server_healthy("localhost", self.mii_config.port_number)
        if self.model is None:
            self.model = MIIClient(self.mii_config)

    def _gen_params_to_mii_params(self, params: Dict):
        """Convert generation parameters to MII parameters."""
        if "max_tokens" in params:
            params["max_new_tokens"] = params["max_tokens"]

        # Remove unsupported keys and log a warning for each
        unsupported_keys = set(params.keys()) - set(MIIGenerationParams.MIIGenerationParams.keys())
        for key in unsupported_keys:
            logger.warning(
                f"Warning: Parameter '{key}' is not supported by MII and will be removed.",
            )
            del params[key]

        return params

    @log_execution_time
    async def generate(self, prompts: List[str], params: Dict) -> List[InferenceResult]:
        """Generate responses for given prompts."""
        if self.model is None:
            logger.warning("MII client not initialized. Initializing now.")
            self.init_client()
        start_time = time.time()
        if isinstance(prompts, str):
            prompts = [prompts]
        try:
            self._gen_params_to_mii_params(params)
            responses = await self.model._request_async_response(prompts, **params)
        except Exception as e:
            raise Exception(
                json.dumps({"error": "Error in processing request", "exception": str(e)}))
        inference_time_ms = (time.time() - start_time) * 1000
        inference_results = []  # type: List[InferenceResult]
        for i, res in enumerate(responses):
            generated_text = res.generated_text
            response_tokens = self.get_tokens(generated_text)
            time_per_token_ms = inference_time_ms / len(response_tokens) if len(response_tokens) > 0 else 0

            result = InferenceResult(
                response=generated_text,
                inference_time_ms=inference_time_ms,
                time_per_token_ms=time_per_token_ms,
                generated_tokens=response_tokens,
                prompt_num=i,
            )
            inference_results.append(result)
        return inference_results

    def _get_mii_config(self):
        """Get MII configuration."""
        default_mii_config = {
            "deployment_name": self.engine_config.mii_config.deployment_name,
            "deployment_type": mii.constants.DeploymentType.AML,
            "instance_type": "",  # this is only used for creating deployment script, can be left empty
            "model_config": {
                "inference_engine_config": {
                    "state_manager": {
                        "max_context": 8192,
                        "max_ragged_batch_size": 768,
                        "max_ragged_sequence_count": 512,
                        "max_tracked_sequences": 2048,
                        "memory_config": {"mode": "reserve", "size": 1000000000},
                        "offload": False,
                    },
                    "tensor_parallel": {"tp_size": self.engine_config.tensor_parallel},
                },
                "max_length": None,
                "model_name_or_path": self.engine_config.model_id,
                "profile_model_time": False,
                "replica_configs": [],
                "replica_num": self.engine_config.num_replicas,
                "sync_debug": False,
                "task": "text-generation",
                "tensor_parallel": self.engine_config.tensor_parallel,
                "tokenizer": self.engine_config.tokenizer,
            },
        }
        mii_config = mii.config.MIIConfig(**default_mii_config)
        return mii_config

    def generate_openai_response(self, request, headers):
        """Mii Engine does not support openai responses."""
        raise NotImplementedError("MII Engine does not support OpenAI APIs")

    async def shutdown_async(self):
        """Terminate DS-MII Server."""
        try:
            await self.model.terminate_async()
        except Exception as e:
            raise Exception(
                json.dumps({"error": "Error in processing request", "exception": str(e)}))
