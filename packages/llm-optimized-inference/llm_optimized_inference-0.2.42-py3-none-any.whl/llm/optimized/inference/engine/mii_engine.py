# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Mii Engine module.

This module contains the MiiEngine class which is responsible for initializing the MII server and client,
generating responses for given prompts, and managing the allocation of processes and load balancing.
"""
import json
import os
import shutil
import time
from typing import Dict, List

import mii
import torch
from llm.optimized.inference.configs import EngineConfig, TaskConfig
from llm.optimized.inference.engine.engine import BaseEngine, InferenceResult
from llm.optimized.inference.logging_config import configure_logger
from llm.optimized.inference.utils import log_execution_time

logger = configure_logger(__name__)


# TODO: Move them to mii config
MAX_TOKENS = int(os.environ.get("MAX_TOTAL_TOKENS", 4096))
MODEL_DIR = os.getenv("AZUREML_MODEL_DIR", "")


class MiiEngine(BaseEngine):
    """Inference engine using MII methods."""

    def __init__(self, config: EngineConfig, task_config: TaskConfig):
        """Initialize the MiiEngine with the given engine and task configurations."""
        self.engine_config = config
        self.task_config = task_config
        self.model = None
        self.mii_config = self._get_mii_config()
        self.custom_model_config_builder = config.custom_model_config_builder
        if self.custom_model_config_builder:
            self.custom_model_config_builder.update_mii_model_config(self.mii_config.model_conf)
        self._file_restructure(self.engine_config.tokenizer, self.engine_config.model_id)

    def load_model(self, env=None):
        """Initialize MII server and MII client."""
        logger.info("MII Config: " + str(self.mii_config))
        logger.info("Start server setup")
        self.mii_server = mii.MIIServer(self.mii_config)
        logger.info("Completed server setup")

    def init_client(self):
        """Initialize the MII client."""
        # wait until server is healthy then create client
        self.wait_until_server_healthy("localhost", self.mii_config.port_number)
        if self.model is None:
            self.model = mii.MIIClient(
                self.mii_config.model_conf.task,
                "localhost",
                self.mii_config.port_number,
            )

    @log_execution_time
    async def generate(self, prompts: List[str], params: Dict) -> List[InferenceResult]:
        """Generate responses for given prompts."""
        if self.model is None:
            logger.warning("MII client not initialized. Initializing now.")
            self.init_client()
        queries = {"query": prompts}
        start_time = time.time()

        if self.custom_model_config_builder:
            # if custom model configuration builder available, then do model level input transformation.
            self.custom_model_config_builder.pre_processing(queries, **params)

        try:
            responses = await self.model._request_async_response(queries, **params)
        except Exception as e:
            raise Exception(json.dumps({"error": "Error in processing request", "exception": str(e)}))
        inference_time_ms = (time.time() - start_time) * 1000

        if self.custom_model_config_builder is not None:
            return self.custom_model_config_builder.post_processing(
                responses, inference_time_ms, prompts=prompts, **params
            )

        inference_results = []  # type: List[InferenceResult]
        return_full_text = params.pop("return_full_text", True)
        for i, res in enumerate(responses.response):
            generated_text = res
            generated_text = self._del_prompt_if_req(prompts[i], generated_text, return_full_text=return_full_text)
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

    def generate_openai_response(self, request, headers):
        """Mii Engine V1 does not support openai responses."""
        raise NotImplementedError("MII V1 Engine does not support OpenAI APIs")

    def _get_mii_config(self):
        """Get MII configuration."""
        # TODO: Remove this once DS-Inference supports 70b models
        is_70b_model = "Llama-2-70b" in MODEL_DIR or "Llama-2-70b-chat" in MODEL_DIR
        replace_with_kernel_inject = not is_70b_model

        default_mii_config = {
            "deployment_name": self.engine_config.mii_config.deployment_name,
            "deployment_type": mii.constants.DeploymentType.AML,
            "instance_type": "",  # this is only used for creating deployment script, can be left empty
            "model_conf": {
                "checkpoint_dict": None,
                "deploy_rank": list(range(self.engine_config.tensor_parallel)),
                "ds_config": self.engine_config.mii_config.ds_config,
                "dtype": torch.float16,
                "enable_cuda_graph": False,
                "enable_deepspeed": self.engine_config.mii_config.enable_deepspeed,
                "enable_zero": self.engine_config.mii_config.ds_zero,
                "hf_auth_token": None,
                "load_with_sys_mem": True,
                "max_tokens": MAX_TOKENS,
                "meta_tensor": False,
                "model": MODEL_DIR,
                "model_path": self.engine_config.model_id,
                "profile_model_time": False,
                "replace_with_kernel_inject": replace_with_kernel_inject,
                "replica_configs": [],
                "replica_num": self.engine_config.num_replicas,
                "skip_model_check": True,
                # "task": self.task_config.task_type,
                "task": "text-generation",
                "tensor_parallel": self.engine_config.tensor_parallel,
                "trust_remote_code": False,
            },
        }
        mii_config = mii.MIIConfig(**default_mii_config)
        return mii_config

    def _file_restructure(self, src: str, dst: str) -> None:
        """Copy all files in one directory to another.

        MII-V1 does not allow to specify both a model and a tokenizer path.
        It expects all tokenizer files to be in the same directory that the model files are in.
        """
        files_to_duplicate = os.listdir(src)
        for file in files_to_duplicate:
            if not os.path.exists(os.path.join(dst, file)):
                shutil.copy(os.path.join(src, file), dst)

    async def shutdown_async(self):
        """Terminate DS-MII Server."""
        try:
            await self.model.terminate_async()
        except Exception as e:
            raise Exception(json.dumps({"error": "Error in processing request", "exception": str(e)}))
