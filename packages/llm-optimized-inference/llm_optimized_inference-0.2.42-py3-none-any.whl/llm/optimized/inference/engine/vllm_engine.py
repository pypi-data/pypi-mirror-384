# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""VLLM Engine module.

This module contains the VLLMEngine class which is responsible for initializing the VLLM server,
generating responses for given prompts, and managing the server processes.
"""

# flake8: noqa

import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Union

import requests
import torch.cuda
from llm.optimized.inference.configs import EngineConfig, TaskConfig
from llm.optimized.inference.constants import (DataTypes, ModelInfo, ModelTypes, VLLMKwargs,
                                               VLLMArgs, VLLMSpecialModels, ExtraParameters)
from llm.optimized.inference.engine import BaseEngine, InferenceResult
from llm.optimized.inference.logging_config import configure_logger
from llm.optimized.inference.utils import log_execution_time
from llm.optimized.inference.api_server_setup.protocol import ChatCompletionRequest, CompletionRequest

logger = configure_logger(__name__)

# fmt: off
VLLM_SAMPLING_PARAMS = {
    "n": "Number of output sequences to return for the given prompt.",
    "best_of": "Number of output sequences that are generated from the prompt. From these `best_of` sequences, the top `n` sequences are returned. `best_of` must be greater than or equal to `n`. This is treated as the beam width when `use_beam_search` is True. By default, `best_of` is set to `n`.",
    "presence_penalty": "Float that penalizes new tokens based on whether they appear in the generated text so far. Values > 0 encourage the model to use new tokens, while values < 0 encourage the model to repeat tokens.",
    "frequency_penalty": "Float that penalizes new tokens based on their frequency in the generated text so far. Values > 0 encourage the model to use new tokens, while values < 0 encourage the model to repeat tokens.",
    "temperature": "Float that controls the randomness of the sampling. Lower values make the model more deterministic, while higher values make the model more random. Zero means greedy sampling.",
    "top_p": "Float that controls the cumulative probability of the top tokens to consider. Must be in (0, 1]. Set to 1 to consider all tokens.",
    "top_k": "Integer that controls the number of top tokens to consider. Set to -1 to consider all tokens.",
    "use_beam_search": "Whether to use beam search instead of sampling.",
    "length_penalty": "Float that penalizes sequences based on their length. Used in beam search.",
    "early_stopping": 'Controls the stopping condition for beam search. It accepts the following values: `True`, where the generation stops as soon as there are `best_of` complete candidates; `False`, where an heuristic is applied and the generation stops when is it very unlikely to find better candidates; `"never"`, where the beam search procedure only stops when there cannot be better candidates (canonical beam search algorithm).',
    "stop": "List of strings that stop the generation when they are generated. The returned output will not contain the stop strings.",
    "stop_token_ids": "List of tokens that stop the generation when they are generated. The returned output will contain the stop tokens unless the stop tokens are special tokens.",
    "ignore_eos": "Whether to ignore the EOS token and continue generating tokens after the EOS token is generated.",
    "max_tokens": "Maximum number of tokens to generate per output sequence.",
    "logprobs": "Number of log probabilities to return per output token.",
    "skip_special_tokens": "Whether to skip special tokens in the output. Defaults to true.",
    "_batch_size": "Number of prompts to generate in parallel. Defaults to 1.",
}


# fmt: on


class VLLMEngine(BaseEngine):
    """VLLM Engine class.

    This class is responsible for initializing the VLLM server, generating responses for given prompts,
    and managing the server processes.
    """

    def __init__(self, engine_config: EngineConfig, task_config: TaskConfig):
        """Initialize the VLLMEngine with the given engine and task configurations."""
        self.engine_config: EngineConfig = engine_config
        self.task_config: TaskConfig = task_config
        self._vllm_config: Dict = self.engine_config.vllm_config or {}
        self._vllm_kwargs: Dict = self.engine_config.vllm_kwargs or {}
        self._model_config: Dict = self.engine_config.model_config or {}
        self._model_type: str = self._model_config.get(ModelInfo.MODEL_TYPE, "")

        # Not all vllm arguments require a value
        self._vllm_args: List = self.engine_config.vllm_args or []
        self._load_vllm_defaults()
        self._verify_and_convert_float_type()
        self._verify_and_modify_tensor_parallel_size()


    @log_execution_time
    def load_model(self, env: Dict = None):
        """Load the model from the pretrained model specified in the engine configuration."""
        if env is None:
            env = os.environ.copy()
        self._start_server(self._vllm_kwargs, self._vllm_args, env=env)

    def init_client(self):
        """Initialize client[s] for the engine to receive requests on."""
        self.wait_until_server_healthy(self._vllm_kwargs[VLLMKwargs.HOST], self._vllm_kwargs[VLLMKwargs.PORT])

    @property
    def server_url(self) -> str:
        """Return the URL of the VLLM server."""
        logger.debug(f"server_url: http://{self._vllm_kwargs[VLLMKwargs.HOST]}:{self._vllm_kwargs[VLLMKwargs.PORT]}")
        return f"http://{self._vllm_kwargs[VLLMKwargs.HOST]}:{self._vllm_kwargs[VLLMKwargs.PORT]}"

    def _load_vllm_defaults(self):
        """Load default values for VLLM server arguments, if not provided."""
        if VLLMKwargs.HOST not in self._vllm_kwargs:
            self._vllm_kwargs[VLLMKwargs.HOST] = self.engine_config.host
        if VLLMKwargs.PORT not in self._vllm_kwargs:
            self._vllm_kwargs[VLLMKwargs.PORT] = self.engine_config.port
        if VLLMKwargs.MODEL not in self._vllm_kwargs:
            self._vllm_kwargs[VLLMKwargs.MODEL] = self.engine_config.model_id
        if VLLMKwargs.TOKENIZER not in self._vllm_kwargs:
            self._vllm_kwargs[VLLMKwargs.TOKENIZER] = self.engine_config.tokenizer
        if VLLMKwargs.TENSOR_PARALLEL_SIZE not in self._vllm_kwargs:
            self._vllm_kwargs[VLLMKwargs.TENSOR_PARALLEL_SIZE] = (
                self.engine_config.tensor_parallel
                if self.engine_config.tensor_parallel is not None
                else torch.cuda.device_count()
            )

        kwargs = {}
        args = []
        if self._vllm_config:
            kwargs = self._vllm_config.get("vllm_kwargs", {})
            args = self._vllm_config.get("vllm_args", [])
            model_settings = self._vllm_config.get("model_settings", {})
        
        # TODO: Remove this once all models adopt inference_config.json
        else:
            model_name = self.engine_config.ml_model_info.get("model_id", None)
            kwargs = VLLMSpecialModels.get_kwargs(self._model_type, model_name)
            args = VLLMSpecialModels.get_args(self._model_type, model_name)
            model_settings = VLLMSpecialModels.get_model_settings(self._model_type)

        for key, val in kwargs.items():
            if key not in self._vllm_kwargs:
                self._vllm_kwargs[key] = val

        for arg in args:
            if arg not in self._vllm_args:
                self._vllm_args.append(arg)
        
        self._vllm_args.append(VLLMArgs.DISABLE_LOG_REQUESTS)
        args_to_env_vars= VLLMArgs.reverse_dict()
        self._vllm_args = list(filter(lambda x: eval(os.getenv(args_to_env_vars[x], "True")), self._vllm_args))
        self._settings = model_settings
        self._update_lora_path_with_model_dir()

    def _verify_and_convert_float_type(self):
        """Check to see whether the model's float type is compatible with the compute type selected.

        Bfloat16 is only supported on GPUs such as A100s. V100s do not support bfloat16, only float16.
        Converting from bfloat16 to float16 is ok in this case.
        """
        # Check if the GPU supports the dtype.
        dtype = self._model_config.get("torch_dtype", DataTypes.AUTO)
        if dtype == DataTypes.BFLOAT16:
            compute_capability = torch.cuda.get_device_capability()
            if compute_capability[0] < 8:
                gpu_name = torch.cuda.get_device_name()

                # Cast bfloat16 to float16
                self._vllm_kwargs[VLLMKwargs.DTYPE] = DataTypes.FLOAT16
                logger.warning(
                    "bfloat16 is only supported on GPUs with compute capability "
                    f"of at least 8.0. Your {gpu_name} GPU has compute capability "
                    f"{compute_capability[0]}.{compute_capability[1]}. "
                    f"bfloat16 will be converted to float16.",
                )

    def _verify_and_modify_tensor_parallel_size(self):
        """Check to see if the tensor parallel size is compatible with the models's number of attention heads."""
        num_attention_heads = self._model_config.get("num_attention_heads", 1)
        num_key_value_heads = self._model_config.get("num_key_value_heads", 1)

        # TODO: Remove if statement once falcon models are updated to latest huggingface commit
        if self._model_type in [ModelTypes.FALCON, ModelTypes.REFINED_WEB, ModelTypes.REFINED_WEB_MODEL]:
            num_attention_heads = self._model_config.get("n_head", 1)
            num_key_value_heads = (
                1 
                if self._model_config.get("multi_query", False) 
                else self._model_config.get("n_head_kv", 1)
            )
        if self._model_type == ModelTypes.DATABRICKS:
            num_attention_heads = self._model_config.get("n_heads", 1)
            num_key_value_heads = self._model_config.get("attn_config", {}).get("kv_n_heads", 1)

        tensor_parallel_size = self._vllm_kwargs[VLLMKwargs.TENSOR_PARALLEL_SIZE]
        new_tensor_parallel_size = tensor_parallel_size
        if tensor_parallel_size != 0:
            while (num_attention_heads % new_tensor_parallel_size != 0 or 
                   num_key_value_heads % new_tensor_parallel_size != 0):
                new_tensor_parallel_size -= 1
        if tensor_parallel_size != new_tensor_parallel_size:
            logger.warning(
                f"Tensor parallel size was incompatible with either the number of attention heads or the number of "
                f"key value heads the model has in its config.json. Number of attention heads ({num_attention_heads})"
                f" and number of key value heads ({num_key_value_heads}) must be divisible by tensor-parallel-size "
                f"({tensor_parallel_size}). To make them compatible, tensor-parallel-size was reduced from "
                f"{tensor_parallel_size} to {new_tensor_parallel_size}."
            )
        self._vllm_kwargs[VLLMKwargs.TENSOR_PARALLEL_SIZE] = new_tensor_parallel_size


    def _start_server(self, server_kwargs: Dict, server_args: List, env: Dict):
        """Start the VLLM server with the given arguments."""
        cmd = ["python", "-m", "llm.optimized.inference.vllm_api_server"]
        for k, v in server_kwargs.items():
            if k in list(VLLMKwargs.vllm_kwargs_with_list_input()) and v:
                cmd.append(f"--{k}")
                cmd.extend(v.split())
            elif v is not None:
                cmd.append(f"--{k}={v}")
        cmd.extend([f"--{arg}" for arg in server_args])
        logger.info(f"Starting VLLM server with command: {cmd}")
        subprocess.Popen(cmd, env=env)
        logger.info("Starting VLLM server...")

    def _get_generate_uri(self) -> str:
        """Get the URI for the generate endpoint of the VLLM server."""
        return f"{self.server_url}/generate"
    
    def _gen_params_to_vllm_params(self, params: Dict) -> Dict:
        """Convert generation parameters to VLLM parameters."""
        if "max_gen_len" in params:
            params["max_tokens"] = params["max_gen_len"]

        if "max_new_tokens" in params:
            params["max_tokens"] = params["max_new_tokens"]

        if "do_sample" in params and not params["do_sample"]:
            logger.info("do_sample is false, setting temperature to 0.")
            params["temperature"] = 0.0

        if "use_beam_search" in params and params["use_beam_search"]:
            logger.info("Beam search is enabled, setting temperature to 0.")
            params["temperature"] = 0.0

            if "best_of" not in params:
                logger.info("Beam search is enabled, setting best_of to 2.")
                params["best_of"] = 2
        
        if "eos_token_id" in params:
            eos_token_id = params["eos_token_id"]
            # eos_token_id in GenerationConfig is (Union[int, List[int]], optional) 
            # while vLLM SamplingParams is (Optional[List[int]])
            if not isinstance(eos_token_id, list):
                params["stop_token_ids"] = [params["eos_token_id"]]
            else:
                params["stop_token_ids"] = params["eos_token_id"]

        # Remove unsupported keys and log a warning for each
        unsupported_keys = set(params.keys()) - set(VLLM_SAMPLING_PARAMS.keys())
        for key in unsupported_keys:
            logger.warning(
                f"Warning: Parameter '{key}' is not supported by VLLM and will be removed.",
            )
            params.pop(key, None)

        return params

    @log_execution_time
    def generate_openai_response(self, request: Union[ChatCompletionRequest, CompletionRequest], headers: Dict):
        """Generate open ai alike responses by calling the openai server api."""
        headers["User-Agent"] = "VLLMEngine Client"
        api_url = f"{self.server_url}/v1/chat/completions"

        if isinstance(request, CompletionRequest):
            api_url = f"{self.server_url}/v1/completions"

        logger.debug(f"generating open ai response with {request}")
        response = requests.post(
            api_url,
            headers=headers,
            json=request.to_downstream_json(headers.get(ExtraParameters.KEY, "") == ExtraParameters.PASS_THROUGH),
            stream=request.stream
        )
        return response

    @log_execution_time
    def generate(self, prompts: List[str], params: Dict) -> List[InferenceResult]:
        """Generate responses for the given prompts with the given parameters."""
        # pop _batch_size from params if it exists, set it to 1 by default (for testing only)
        batch_size = params.pop("_batch_size", 1)
        # we need to pop and pass in return_full_text by itself as well, since its not a vLLM official param
        return_full_text = params.pop("return_full_text", True)
        
        results = []
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            results = list(
                executor.map(
                    lambda prompt: self._generate_single_prompt(prompt, params, return_full_text),
                    prompts,
                ),
            )
        inference_time_ms = (time.time() - start_time) * 1000
        for i, result in enumerate(results):
            result.inference_time_ms = inference_time_ms
            result.prompt_num = i
        return results

    @log_execution_time
    def _generate_single_prompt(self, prompt: str, params: Dict, return_full_text: bool) -> InferenceResult:
        """Generate a response for a single prompt with the given parameters."""
        api_url = self._get_generate_uri()

        params = self._gen_params_to_vllm_params(params)
        
        generate_openai_response = "false"
        if self._settings.get("generate-openai-response", False):
            generate_openai_response = "true"

        headers = {
            "User-Agent": "VLLMEngine Client",
            "generate_openai_response": generate_openai_response
        }

        payload = {
            "prompt": prompt,
            **params,
            "stream": False,
        }
       
        start_time = time.time()
        response = requests.post(api_url, headers=headers, json=payload)
        end_time = time.time()
        if response.status_code == 200:
            # take the first candidate from the list of candidates (if beam search was used)
            output = json.loads(response.content)
            prompt_tokens, completion_tokens = None, None
            is_oai_resp = False
            if "text" in output:
                generated_text = output["text"][0]
            else:
                # assume openai response format
                is_oai_resp = True
                generated_text = output["choices"][0]["message"]["content"]
                prompt_tokens = output["usage"]["prompt_tokens"]
                completion_tokens = output["usage"]["completion_tokens"]
            generated_text = generated_text if is_oai_resp else self._del_prompt_if_req(prompt, generated_text, return_full_text=return_full_text)
            inference_time_ms = (end_time - start_time) * 1000
            response_tokens = self.get_tokens(generated_text)
            time_per_token_ms = inference_time_ms / len(response_tokens) if len(response_tokens) > 0 else 0
            # TODO: setting inference_time_ms to None until mii inference time can also be recorded per prompt
            res = InferenceResult(
                generated_text, None, time_per_token_ms, response_tokens, 0,
                n_prompt_tokens=prompt_tokens, n_completion_tokens=completion_tokens
                )
        else:
            res = InferenceResult(None, None, None, None, None, error=response.content)

        return res
    
    async def shutdown_async(self):
        """Terminate DS-MII Server."""
        # empty function as we do not need to terminate the ds-mii server when the vllm engine is used
        return


    def _update_lora_path_with_model_dir(self):
        updated_lora_path = []
        if VLLMKwargs.LORA_MODULES in self._vllm_kwargs:
            lora_modules = self._vllm_kwargs[VLLMKwargs.LORA_MODULES]
            model_dir = os.getenv("AZUREML_MODEL_DIR")
            if lora_modules:
                lora_paths = lora_modules.split(" ")
                for path in lora_paths:
                    key_value = path.split("=")
                    if len(key_value) == 2:
                        key, relative_path = key_value
                        resolved_path = os.path.join(str(model_dir), str(relative_path))
                        updated_lora_path.append(f"{key}={resolved_path}")
                    else:
                        raise ValueError(f"Invalid format in LoRA module path: '{path}'. Expected 'key=value'.")

                self._vllm_kwargs[VLLMKwargs.LORA_MODULES]=" ".join(updated_lora_path)

