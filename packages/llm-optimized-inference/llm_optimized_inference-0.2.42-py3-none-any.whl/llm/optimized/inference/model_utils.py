# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""This module provides mlflow model realted utilities."""
import json
import math
import os
import re
import torch

from llm.optimized.inference.constants import (SupportedTask,
                                               ALL_TASKS,
                                               TaskType,
                                               VLLM_MII_TASKS,
                                               MetaData,
                                               ModelInfo)
from llm.optimized.inference.constants import EngineName, VLLMSupportedModels, MIISupportedModels
from llm.optimized.inference.model_config_factory import ModelConfigFactory
from llm.optimized.inference.utils import map_env_vars_to_vllm_server_kwargs, map_env_vars_to_vllm_server_args
from llm.optimized.inference.logging_config import configure_logger
from copy import deepcopy
from typing import Dict

logger = configure_logger(__name__)

FILE_FILTER = re.compile(r'^(?!.*\.bin$)(?:model-.*\.safetensors|.*(?<!\.safetensors))$')


def get_generator_params(params: Dict):
    """Return accumulated generator params."""
    updated_params = {}
    # map 'max_gen_len' to 'max_new_tokens' if present
    if "max_gen_len" in params:
        logger.warning("max_gen_len is deprecated. Use max_new_tokens")
        params["max_new_tokens"] = params["max_gen_len"]
        del params["max_gen_len"]

    updated_params.update(params)
    return updated_params


def get_best_engine(config_path, inference_config_path):
    """Get best engine."""
    if inference_config_path is not None and os.path.exists(inference_config_path):
        inference_config = {}
        with open(inference_config_path) as inference_content:
            inference_config = json.load(inference_content)
        inference_engine = inference_config["inference_engine"]
        logger.info("Using engine: {}".format(inference_engine))
        return inference_engine

    # TODO: Remove the rest of this function once all models adopt inference_config.json
    if not os.path.exists(config_path):
        logger.info("No config file found.\
                    Passing the default HF engine as best engine.")
        logger.info("Using engine: {}".format(EngineName.HF))
        return EngineName.HF
    with open(config_path) as f:
        model_config = json.load(f)
    model_class = model_config["architectures"][0]
    best_engine = EngineName.HF
    if model_class in VLLMSupportedModels.Models:
        best_engine = EngineName.VLLM
    elif model_class in MIISupportedModels.Models:
        best_engine = EngineName.MII
    logger.info("Using engine: {}".format(best_engine))
    return best_engine


def build_configs_from_model(mlmodel, model_path, config_path, tokenizer_path, inference_config_path=None):
    """Build engine and task config from mlflow model."""
    default_generator_configs = ""
    ml_model_info = {}

    default_engine = get_best_engine(config_path, inference_config_path)
    tensor_parallel = os.getenv("TENSOR_PARALLEL", None)
    if tensor_parallel:
        try:
            tensor_parallel = int(tensor_parallel)
        except ValueError:
            tensor_parallel = None
    engine_config = {
        "engine_name": os.getenv("ENGINE_NAME", default_engine),
        "model_id": model_path,
        "tensor_parallel": tensor_parallel
    }
    engine_config["hf_config_path"] = os.path.dirname(config_path)
    engine_config["tokenizer"] = tokenizer_path
    task_config = {}
    model_info = {}

    if mlmodel:
        flavors = mlmodel.get("flavors", {})

        # update default gen configs with model configs
        model_generator_configs = {}
        if os.path.exists(os.path.join(model_path, "generation_config.json")):
            with open(os.path.join(model_path, "generation_config.json")) as f:
                model_generator_configs.update(json.load(f))
        default_generator_configs = get_generator_params(
            model_generator_configs
        )

        if "transformers" in flavors:
            task_type = flavors["transformers"]["task"]
            flavors_dict = flavors.get("transformers")
            ml_model_info = deepcopy(flavors_dict)
            if ml_model_info.get("tokenizer_type", None):
                ml_model_info["hf_tokenizer_class"] = ml_model_info.get("tokenizer_type")
            if ml_model_info.get("pipeline_model_type", None):
                ml_model_info["hf_pretrained_class"] = ml_model_info.get("pipeline_model_type")
        elif "hftransformersv2" in flavors:
            task_type = flavors["hftransformersv2"]["task_type"]
            ml_model_info = flavors["hftransformersv2"].copy()
            if task_type not in ALL_TASKS:
                raise Exception(f"Unsupported task_type {task_type}")
        elif "python_function" in flavors:
            task_type = mlmodel["metadata"]["base_model_task"]
            if task_type not in [TaskType.TEXT_TO_IMAGE, TaskType.TEXT_TO_IMAGE_INPAINTING, TaskType.CHAT_COMPLETION]:
                raise Exception(f"Unsupported task_type {task_type}")

            if task_type in [TaskType.TEXT_TO_IMAGE, TaskType.TEXT_TO_IMAGE_INPAINTING]:
                model_type = mlmodel["metadata"].get("model_type", "")

                model_config_builder = ModelConfigFactory.get_config_builder(task=task_type, model_type=model_type)
                engine_config.update(
                    {
                        "engine_name": model_config_builder.engine,
                        "mii_config": model_config_builder.get_optimization_config(),
                        "custom_model_config_builder": model_config_builder,
                        "model_id": os.path.join(os.getenv("AZUREML_MODEL_DIR", ""), model_config_builder.model_path),
                        "tokenizer": os.path.join(os.getenv("AZUREML_MODEL_DIR", ""),
                                                  model_config_builder.MLFLOW_MODEL_PATH,
                                                  "tokenizer"),
                        "tensor_parallel": model_config_builder.tensor_parallel
                    }
                )
                task_config = model_config_builder.get_task_config()

        # get model info
        metadata = mlmodel.get("metadata", {})
        model_info[ModelInfo.MODEL_TYPE] = task_type
        model_info[ModelInfo.MODEL_NAME] = metadata.get(MetaData.MODEL_NAME, "")
        model_info[ModelInfo.MODEL_PROVIDER] = metadata.get(MetaData.MODEL_PROVIDER, "")
        model_info[MetaData.IS_COMMON_API_ENABLED] = metadata.get(MetaData.IS_COMMON_API_ENABLED, False)

    if task_type != TaskType.TEXT_TO_IMAGE:
        if engine_config["engine_name"] in [EngineName.MII, EngineName.VLLM] and task_type not in VLLM_MII_TASKS:
            engine_config["engine_name"] = EngineName.HF

    if engine_config["engine_name"] == EngineName.MII or engine_config["engine_name"] == EngineName.MII_V1:
        mii_engine_config = {
            "deployment_name": os.getenv("DEPLOYMENT_NAME", "llama-deployment"),
            "mii_configs": {},
        }

        engine_config["mii_config"] = mii_engine_config

    if engine_config["engine_name"] == EngineName.VLLM:
        model_config = {}
        vllm_config = {}
        vllm_kwargs = map_env_vars_to_vllm_server_kwargs()
        vllm_args = map_env_vars_to_vllm_server_args()
        if config_path and os.path.exists(config_path):
            with open(config_path) as config_content:
                model_config = json.load(config_content)

        if inference_config_path is not None and os.path.exists(inference_config_path):
            with open(inference_config_path) as inference_content:
                vllm_config = json.load(inference_content)

        engine_config["vllm_config"] = vllm_config
        engine_config["vllm_kwargs"] = vllm_kwargs
        engine_config["vllm_args"] = vllm_args
        engine_config["model_config"] = model_config

        _load_inference_model_type(model_config)

    engine_config["ml_model_info"] = ml_model_info

    task_config = {
        "task_type": TaskType.CONVERSATIONAL
        if task_type == SupportedTask.CHAT_COMPLETION
        else task_type,
    }
    return engine_config, task_config, default_generator_configs, task_type, model_info


def build_model_config_for_vllm(model_path):
    """Build model config for vllm."""
    config_path = os.path.join(model_path, "config.json")
    inference_config_path = os.path.join(model_path, "inference_config.json")
    task_type = _get_task_type()
    tensor_parallel = _get_tensor_parallel()
    model_config = _load_json_if_exists(config_path)

    engine_config = {
        "engine_name": EngineName.VLLM,
        "model_id": model_path,
        "tensor_parallel": tensor_parallel,
        "hf_config_path": os.path.dirname(config_path),
        "tokenizer": model_path,
        "ml_model_info": {},  # Keeping to maintain compatibility with existing code
        "vllm_config": _load_json_if_exists(inference_config_path),
        "vllm_kwargs": map_env_vars_to_vllm_server_kwargs(),
        "vllm_args": map_env_vars_to_vllm_server_args(),
        "model_config": model_config
    }

    _load_inference_model_type(model_config)

    task_config = {
        "task_type": TaskType.CONVERSATIONAL if task_type == SupportedTask.CHAT_COMPLETION else task_type,
    }

    gen_config_path = os.path.join(model_path, "generation_config.json")
    model_generator_configs = _load_json_if_exists(gen_config_path)
    default_generator_configs = get_generator_params(model_generator_configs)

    # Model info
    model_info = {
        ModelInfo.MODEL_TYPE: task_type,
        ModelInfo.MODEL_NAME: os.getenv("MODEL_NAME", ""),
        ModelInfo.MODEL_PROVIDER: os.getenv("MODEL_PROVIDER", ""),
        MetaData.IS_COMMON_API_ENABLED: os.getenv("IS_COMMON_API_ENABLED", False),
    }

    return engine_config, task_config, default_generator_configs, task_type, model_info


def get_model_size_in_gb(model_path: str) -> int:
    """Get the estimated model size in GB."""
    total_size = 0
    for file in os.listdir(model_path):
        if re.match(FILE_FILTER, file):
            file_path = os.path.join(model_path, file)
            file_size = os.path.getsize(file_path)
            total_size += file_size
    # Return the total size rounded up
    return math.ceil(total_size / (1024**3))


def verify_model_fits_in_gpu(model_size, tensor_parallel, quantization=False):
    """Check if the model can fit with the givens sku and tensor parallel."""
    gpu_size_in_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)

    # TODO: Find a better mapping for this. Only snowflake models quantize and it roughly cuts the model
    # size in half.
    if quantization:
        model_size /= 2

    # Leave memory for KV Cache
    memory_available = (gpu_size_in_gb * tensor_parallel) * 0.8
    if memory_available < model_size:
        logger.debug(
            "Model does not fit with extra room for KV Cache. Calculating without extra memory for cache.",
        )
        # Try with no memory left for KV Cache
        total_memory = gpu_size_in_gb * tensor_parallel
        if total_memory < model_size:
            raise ValueError(f"Model will not fit in the sku with tensor parallel of {tensor_parallel}. "
                             f"Consider choosing a larger sku or increasing the tensor parallel if possible.")


def _load_inference_model_type(model_config):
    """Load inferencemodel type in environment variable."""
    model_type = model_config.get("model_type", None)
    logger.info(f"Inference model type for loaded model is {model_type}")
    if model_type:
        os.environ["INFERENCE_MODEL_TYPE"] = model_type


def _get_tensor_parallel():
    """Get tensor parallel from environment variable."""
    tensor_parallel = os.getenv("TENSOR_PARALLEL", None)
    if tensor_parallel:
        try:
            tensor_parallel = int(tensor_parallel)
        except ValueError:
            logger.warning("Invalid TENSOR_PARALLEL value. It should be an integer.")
            tensor_parallel = None
    return tensor_parallel


def _get_task_type():
    """Get task type from environment variable."""
    task_type = os.getenv("TASK_TYPE", None)
    if not task_type:
        raise ValueError("TASK_TYPE environment variable is not set. Please set it to a valid task type.")
    if task_type not in [SupportedTask.CHAT_COMPLETION, SupportedTask.TEXT_GENERATION]:
        raise ValueError(f"Unsupported task_type {task_type}. Supported tasks are:"
                         f"{[SupportedTask.CHAT_COMPLETION, SupportedTask.TEXT_GENERATION]}")
    return task_type


def _load_json_if_exists(path):
    if path and os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}
