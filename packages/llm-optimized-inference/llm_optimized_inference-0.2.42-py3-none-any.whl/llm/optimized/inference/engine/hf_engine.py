# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""HF Engine module.

This module contains the HfEngine class which is responsible for initializing the huggingface pipeline API,
generating responses for given inputs.
"""

from llm.optimized.inference.engine import BaseEngine, InferenceResult
from llm.optimized.inference.utils import log_execution_time
from llm.optimized.inference.configs import EngineConfig, TaskConfig
from llm.optimized.inference.logging_config import configure_logger
from llm.optimized.inference.engine._hf_predictors import get_predictor
from llm.optimized.inference.constants import TaskType
import pandas as pd
import torch # noqa

from typing import List, Dict

import time
import importlib

logger = configure_logger(__name__)


def sanitize_load_args(items):
    """Validate model load arguments."""
    for item in items:
        if isinstance(items[item], str) and items[item].startswith("torch."):
            items[item] = eval(items[item])
    return items


class HfEngine(BaseEngine):
    """Inference engine using Hugging Face methods."""

    def __init__(self, engine_config: EngineConfig, task_config: TaskConfig):
        """Initialize the HfEngine with the given engine configuration."""
        self.engine_config = engine_config
        self.task_config = task_config
        self.config_kwargs = {}
        self.config_class_name = "AutoConfig"
        self.tokenizer_kwargs = {}
        self.tokenizer_class_name = "AutoTokenizer"
        self.model_kwargs = {}
        self.model_class_name = "AutoModel"
        self.model_loaded = False

    def _get_object_from_module(self, class_name):
        module_name = "transformers"
        try:
            model_module = importlib.import_module(module_name)
            object_class = getattr(model_module, class_name)
        except (AttributeError, ImportError) as exc:
            message = "Failed to import {} class from {} \
                       with error {}".format(class_name, module_name, repr(exc))
            logger.error(message)
            raise exc
        return object_class

    def _fetch_load_data_from_info(self):
        if self.engine_config.ml_model_info:
            self.config_kwargs = self.engine_config.ml_model_info.get(
                "config_hf_load_kwargs", {"trust_remote_code": True}
            )
            self.model_kwargs = self.engine_config.ml_model_info.get(
                "model_hf_load_kwargs", {"trust_remote_code": True}
            )
            self.tokenizer_kwargs = self.engine_config.ml_model_info.get(
                "tokenizer_hf_load_kwargs", {"trust_remote_code": True}
            )
            self.config_class_name = self.engine_config.ml_model_info.get(
                "hf_config_class", self.config_class_name
            )
            self.tokenizer_class_name = self.engine_config.ml_model_info.get(
                "hf_tokenizer_class", self.tokenizer_class_name
            )
            self.model_class_name = self.engine_config.ml_model_info.get(
                "hf_pretrained_class", self.model_class_name
            )

    def init_client(self):
        """Init Client."""
        if not self.model_loaded:
            self.load_model({})

    @log_execution_time
    def load_model(self, env: Dict = None):
        """Load the model from the pretrained model specified in the engine configuration."""
        visible_devices = env.get("CUDA_VISIBLE_DEVICES", "")
        logger.info(f"Cuda visible devices: {visible_devices}")
        self.loaded_model_device = ""
        self._fetch_load_data_from_info()
        if len(visible_devices.split(",")) > 1 or len(visible_devices) == 0:
            self.model_kwargs["device_map"] = "auto"
            self.loaded_model_device = "auto"
        else:
            self.model_kwargs["device_map"] = int(visible_devices)
            self.loaded_model_device = int(visible_devices)
        logger.info(f"Model load args: {self.model_kwargs}")
        self.config = self._get_object_from_module(self.config_class_name).from_pretrained(
            self.engine_config.hf_config_path,
            **sanitize_load_args(self.config_kwargs)
        )
        self.tokenizer = self._get_object_from_module(self.tokenizer_class_name).from_pretrained(
            self.engine_config.tokenizer,
            **sanitize_load_args(self.tokenizer_kwargs)
        )
        try:
            self.model = self._get_object_from_module(self.model_class_name).from_pretrained(
                self.engine_config.model_id, config=self.config,
                **sanitize_load_args(self.model_kwargs)
            )
        except (ValueError, NotImplementedError) as e:
            logger.info(f"Model isn't compatible with deepspeed and latest \
                        pytorch. Offloading it to CPU. Full Error: {repr(e)}")
            self.model_kwargs.pop("device_map")
            self.model_kwargs["low_cpu_mem_usage"] = False
            # self.model_kwargs["device"] = int(visible_devices) if torch.cuda.is_available() else -1
            logger.info(f"Passing Device Model kwargs: {self.model_kwargs}")
            self.model = self._get_object_from_module(self.model_class_name).from_pretrained(
                self.engine_config.model_id, config=self.config,
                **sanitize_load_args(self.model_kwargs)
            )
            if len(visible_devices) == 1:
                self.model.to("cuda:" + str(visible_devices))
            self.loaded_model_device = self.model.device
        except Exception as e:
            logger.warning(f"Failed to load the model with exception: {repr(e)}")
            raise e
        logger.info(f"Model Device: {self.model.device}")
        self.model_loaded = True

    def _get_problem_type(self):
        if hasattr(self.config, "problem_type"):
            return self.config.problem_type
        return None

    @log_execution_time
    def generate_openai_response(self, request, headers):
        """Generate open ai alike responses by calling the openai server api."""
        return super().generate_openai_response(request, headers)

    @log_execution_time
    def generate(self, prompts: List[str], params: Dict) -> List[InferenceResult]:
        """Generate responses for given prompts."""
        if not self.model_loaded:
            self.load_model({})
        df = pd.DataFrame(prompts)
        st = time.time()
        predictor_cls = get_predictor(task_type=self.task_config.task_type, problem_type=self._get_problem_type())
        predictor_obj = predictor_cls(task_type=self.task_config.task_type, model=self.model,
                                      tokenizer=self.tokenizer, config=self.config)
        pred_probas = None
        if self.task_config.task_type in (TaskType.TEXT_GENERATION, TaskType.CONVERSATIONAL, TaskType.CHAT_COMPLETION):
            preds = predictor_obj.predict(
                df,
                generator_config=params,
                pipeline_init_args={"device_map": self.loaded_model_device}
            )
        elif self.task_config.task_type == TaskType.TEXT_CLASSIFICATION:
            preds, pred_probas = predictor_obj.predict(
                df,
                tokenizer_config=params,
                pipeline_init_args={"device_map": self.loaded_model_device}
            )
            if isinstance(pred_probas, pd.DataFrame):
                pred_probas = pred_probas.values.tolist()
            if isinstance(pred_probas, pd.Series):
                pred_probas = pred_probas.to_list()
        else:
            preds = predictor_obj.predict(df, tokenizer_config=params,
                                          pipeline_init_args={"device_map": self.loaded_model_device})
        et = time.time()
        inference_time_ms = (et - st) * 1000 / len(prompts)
        num_tokens = len(preds[0])
        time_per_token_ms = (
            inference_time_ms / num_tokens if num_tokens > 0 else 0
        )
        result = []
        for ind, generated_text in enumerate(preds.values.tolist()):
            res = InferenceResult(
                response=generated_text[0],
                inference_time_ms=inference_time_ms,
                time_per_token_ms=time_per_token_ms,
                generated_tokens=[],
                prompt_num=ind,
                scores=pred_probas[ind] if self.task_config.task_type == TaskType.TEXT_CLASSIFICATION else None
            )
            result.append(res)
        return result

    async def shutdown_async(self):
        """Terminate DS-MII Server."""
        # empty function as we do not need to terminate the ds-mii server when the vllm engine is used
        return
