# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""This module defines the EngineName and TaskType enums."""
from enum import Enum
from typing import Dict, List, Optional


class EngineName(str, Enum):
    """Enum representing the names of the engines."""

    HF = "hf"
    VLLM = "vllm"
    MII = "mii"
    MII_V1 = "mii-v1"

    def __str__(self):
        """Return the string representation of the engine name."""
        return self.value


class ExtraParameters:
    """Extra parameter options."""

    KEY = "extra-parameters"
    ERROR = "error"
    DROP = "drop"
    PASS_THROUGH = "pass-through"
    OPTIONS = [ERROR, DROP, PASS_THROUGH]


class CommonAPI:
    """Common api constants."""

    CHAT_COMPLETION_TAG = "chat-completion"

    MODELS_TAGGS_MAPPING = {
        "mistralai/Mistral-7B-Instruct-v0.2": CHAT_COMPLETION_TAG,
        "mistralai/Mixtral-8x7B-Instruct-v0.1": CHAT_COMPLETION_TAG,
        "mistralai/Mixtral-8x22B-Instruct-v0.1": CHAT_COMPLETION_TAG,
        "Llama-2-7b-chat": CHAT_COMPLETION_TAG,
        "Llama-2-13b-chat": CHAT_COMPLETION_TAG,
        "Llama-2-70b-chat": CHAT_COMPLETION_TAG,
        "Meta-Llama-3-8B-Instruct": CHAT_COMPLETION_TAG,
        "Meta-Llama-3-70B-Instruct": CHAT_COMPLETION_TAG,
        "Phi-3-mini-4k-instruct": CHAT_COMPLETION_TAG,
        "Phi-3-mini-128k-instruct": CHAT_COMPLETION_TAG,
        "Phi-3-medium-4k-instruct": CHAT_COMPLETION_TAG,
        "Phi-3-medium-128k-instruct": CHAT_COMPLETION_TAG,
        "Phi-3-small-8k-instruct": CHAT_COMPLETION_TAG,
        "Phi-3-small-128k-instruct": CHAT_COMPLETION_TAG,
        "Phi-3-vision-128k-instruct": CHAT_COMPLETION_TAG,
        "Llama-Guard-3-8B": CHAT_COMPLETION_TAG,
        "Phi-3.5-mini-128k-instruct": CHAT_COMPLETION_TAG,
        "Phi-3.5-vision-128k-instruct": CHAT_COMPLETION_TAG,
        "Phi-3.5-MoE-128k-Instruct": CHAT_COMPLETION_TAG
    }


class MetaData:
    """metadata keys."""

    MODEL_NAME = "base_model_name"
    MODEL_PROVIDER = "model_provider_name"
    IS_COMMON_API_ENABLED = "is_common_api_enabled"


class ModelInfo:
    """Model info."""

    MODEL_NAME = "model_name"
    MODEL_PROVIDER = "model_provider_name"
    MODEL_TYPE = "model_type"


class TaskType(str, Enum):
    """Enum representing the types of tasks."""

    TEXT_GENERATION = "text-generation"
    CONVERSATIONAL = "conversational"
    TEXT_TO_IMAGE = "text-to-image"
    TEXT_CLASSIFICATION = "text-classification"
    TEXT_CLASSIFICATION_MULTILABEL = "text-classification-multilabel"
    NER = "text-named-entity-recognition"
    SUMMARIZATION = "text-summarization"
    QnA = "question-answering"
    TRANSLATION = "text-translation"
    TEXT_GENERATION_CODE = "text-generation-code"
    FILL_MASK = "fill-mask"
    CHAT_COMPLETION = "chat-completion"
    TEXT_TO_IMAGE_INPAINTING = "text-to-image-inpainting"

    def __str__(self):
        """Return the string representation of the task type."""
        return self.value


class SupportedTask:
    """Supported tasks by text-generation-inference."""

    TEXT_GENERATION = "text-generation"
    CHAT_COMPLETION = "chat-completion"
    TEXT_TO_IMAGE = "text-to-image"
    TEXT_CLASSIFICATION = "text-classification"
    TEXT_CLASSIFICATION_MULTILABEL = "text-classification-multilabel"
    NER = "token-classification"
    SUMMARIZATION = "summarization"
    QnA = "question-answering"
    TRANSLATION = "translation"
    TEXT_GENERATION_CODE = "text-generation-code"
    FILL_MASK = "fill-mask"
    TEXT_TO_IMAGE_INPAINTING = "text-to-image-inpainting"


class ServerSetupParams:
    """Parameters for setting up the server."""

    WAIT_TIME_MIN = 15  # time to wait for the server to become healthy
    DEFAULT_WORKER_COUNT = 1


class VLLMSupportedModels:
    """VLLM Supported Models List."""

    # TODO: Remove this class once inference_config.json is adopted by all models

    Models = {
        "ArcticForCausalLM",
        "AquilaForCausalLM",
        "BaiChuanForCausalLM",
        "BloomForCausalLM",
        "ChatGLMModel",
        "DeciLMForCausalLM",
        "FalconForCausalLM",
        "GemmaForCausalLM",
        "GPT2LMHeadModel",
        "GPTBigCodeForCausalLM",
        "GPTJForCausalLM",
        "GPTNeoXForCausalLM",
        "InternLMForCausalLM",
        "InternLM2ForCausalLM",
        "LlamaForCausalLM",
        "MistralForCausalLM",
        "MixtralForCausalLM",
        "MPTForCausalLM",
        "OLMoForCausalLM",
        "OPTForCausalLM",
        "OrionForCausalLM",
        "QWenLMHeadModel",
        "Qwen2ForCausalLM",
        "RWForCausalLM",
        "StableLmForCausalLM",
        "DbrxForCausalLM",
        "PhiForCausalLM",
        "Phi3ForCausalLM",
        "Phi3VForCausalLM",
        "Phi3SmallForCausalLM",
        "Phi3VForCausalLM",
        "YakForCausalLM",
        "MllamaForConditionalGeneration",
        "PhiOForCausalLM"
    }


class MIISupportedModels:
    """MII Supported Models."""

    # TODO: Add more models from different tasks
    # TODO: Remove this class once inference_config.json is adopted by all models

    Models = {
        "BloomForCausalLM",
        "GPT2LMHeadModel",
        "GPTBigCodeForCausalLM",
        "GPTJForCausalLM",
        "GPTNeoXForCausalLM",
        "LlamaForCausalLM",
        "OPTForCausalLM",
        "FalconForCausalLM",
        "MistralForCausalLM",
        "MixtralForCausalLM",
        "PhiForCausalLM",
        "QWenLMHeadModel"
    }


class VLLMSpecialModels:
    """Models Types that require additional parameters to work with vllm."""

    # TODO: Remove this class once inference_config.json is adopted by all models

    ModelTypes = {
        "falcon": {"kwargs": {"gpu-memory-utilization": .95}, "args": ["trust-remote-code"]},
        "RefinedWebModel": {"kwargs": {"gpu-memory-utilization": .95}, "args": ["trust-remote-code"]},
        "RefinedWeb": {"kwargs": {"gpu-memory-utilization": .95}, "args": ["trust-remote-code"]},
        "dbrx": {"args": ["trust-remote-code"]},
        "deci_lm": {"args": ["trust-remote-code"]},
        "phi": {"args": ["trust-remote-code"]},
        "phi3": {"kwargs": {"tensor-parallel-size": 1}, "args": ["trust-remote-code"]},
        "phi3small": {"kwargs": {"tensor-parallel-size": 1}, "args": ["trust-remote-code"]},
        "phi3_v": {
            "kwargs": {"tensor-parallel-size": 2, "gpu-memory-utilization": .95},
            # disable-frontend-multiprocessing is temp work around for vllm bug
            # https://github.com/vllm-project/vllm/issues/8288
            "args": ["trust-remote-code", "disable-frontend-multiprocessing"],
            "model_settings": {"generate-openai-response": True}
        },
        "yak": {"kwargs": {"quantization": "yq"}},
        "artic": {"kwargs": {"quantization": "deepspeedfp"}, "args": ["trust-remote-code"]}
    }

    Models = {
        "microsoft/phi-3-mini-4k-instruct": {"kwargs": {"tensor-parallel-size": 1}},
        "microsoft/phi-3-mini-128k-instruct": {"kwargs": {"tensor-parallel-size": 1}},
        "microsoft/phi-3-small-8k-instruct": {"kwargs": {"tensor-parallel-size": 1}},
        # enable-chunked-prefill is to temp work around for vllm bug
        # https://github.com/vllm-project/vllm/issues/7787
        "microsoft/phi-3-small-128k-instruct": {"kwargs": {"tensor-parallel-size": 1,
                                                           "enable-chunked-prefill": False}},
        "microsoft/phi-3-medium-4k-instruct": {"kwargs": {"tensor-parallel-size": 1}},
        "microsoft/phi-3-medium-128k-instruct": {"kwargs": {"tensor-parallel-size": 2}}
    }

    @classmethod
    def get_kwargs(cls, model_type: str, model_name: Optional[str]) -> Dict:
        """Get the kwargs the vllm server needs for the given model."""
        kwargs = cls.ModelTypes.get(model_type, {}).get("kwargs", {})
        print(f"#####modelname: {model_name}")
        model_specific_kwargs = cls.Models.get(model_name, {}).get("kwargs", {})
        kwargs.update(model_specific_kwargs)
        return kwargs

    @classmethod
    def get_model_settings(cls, model_type: str) -> Dict:
        """Get the kwargs the vllm server needs for the given model."""
        model_settings = cls.ModelTypes.get(model_type, {}).get("model_settings", {})
        return model_settings

    @classmethod
    def get_args(cls, model_type: str, model_name: Optional[str]) -> List:
        """Get the args the vllm server needs for the given model."""
        args = cls.ModelTypes.get(model_type, {}).get("args", [])
        model_specific_args = cls.Models.get(model_name, {}).get("args", [])
        args.extend(model_specific_args)
        return args


class MIIGenerationParams:
    """MII Generation Parameters."""

    MIIGenerationParams = {
        "prompt_length": ("Length of the input prompt. Autopopulated when creating requests, any user-provided values"
                          " will be ignored."),
        "max_length": "Maximum length of `input_tokens` + `generated_tokens`.",
        "max_new_tokens": "Maximum number of new tokens generated. `max_length` takes precedent.",
        "min_new_tokens": "Minimum number of new tokens generated.",
        "stream": "Enable streaming output.",
        "ignore_eos": "Ignore EoS token and continue generating text until we reach `max_length` or`max_new_tokens`.",
        "return_full_text": "Prepends the input prompt to the generated text.",
        "do_sample": "When `False`, do greedy sampling.",
        "top_p": "Top P value.",
        "top_k": "Top K value.",
        "temperature": "Temperature value.",
        "stop": "List of strings to stop generation at."
    }


ALL_TASKS = [
    SupportedTask.TEXT_TO_IMAGE,
    SupportedTask.TEXT_CLASSIFICATION,
    SupportedTask.TEXT_CLASSIFICATION_MULTILABEL,
    SupportedTask.NER,
    SupportedTask.SUMMARIZATION,
    SupportedTask.QnA,
    SupportedTask.TRANSLATION,
    SupportedTask.FILL_MASK,
    SupportedTask.TEXT_GENERATION,
    SupportedTask.CHAT_COMPLETION,
]

VLLM_MII_TASKS = [
    SupportedTask.TEXT_GENERATION,
    SupportedTask.CHAT_COMPLETION,
    TaskType.CONVERSATIONAL
]

MULTILABEL_SET = [
    SupportedTask.TEXT_CLASSIFICATION_MULTILABEL,
]

CLASSIFICATION_SET = [
    SupportedTask.TEXT_CLASSIFICATION,
    SupportedTask.TEXT_CLASSIFICATION_MULTILABEL
]

MULTIPLE_OUTPUTS_SET = [
    SupportedTask.NER,
    SupportedTask.TEXT_CLASSIFICATION_MULTILABEL
]


class ModelTypes:
    """Model types."""

    PHI3_V = "phi3_v"
    FALCON = "falcon"
    DATABRICKS = "dbrx"
    REFINED_WEB = "RefinedWeb"
    REFINED_WEB_MODEL = "RefinedWebModel"
    LLAMA_VISION_TEXT = "mllama"
    PHIO = "phio"


class VLLMArgs:
    """Vllm server arguments."""

    SKIP_TOKENIZER_INIT = "skip-tokenizer-init"
    TRUST_REMOTE_CODE = "trust-remote-code"
    WORKER_USE_RAY = "worker-use-ray"
    RAY_WORKERS_USE_NSIGHT = "ray-workers-use-nsight"
    ENABLE_PREFIX_CACHING = "enable-prefix-caching"
    DISABLE_SLIDING_WINDOW = "disable-sliding-window"
    USE_V2_BLOCK_MANAGER = "use-v2-block-manager"
    DISABLE_LOG_STATS = "disable-log-stats"
    ENFORCE_EAGER = "enforce-eager"
    DISABLE_CUSTOM_ALL_REDUCE = "disable-custom-all-reduce"
    ENABLE_LORA = "enable-lora"
    FULLY_SHARDED_LORAS = "fully-sharded-loras"
    ENABLE_CHUNCKED_PREFILL = "enable-chunked-prefill"
    DISABLE_LOG_REQUESTS = "disable-log-requests"
    ENGINE_USE_RAY = "engine-use-ray"
    DISABLE_FRONTEND_MULTIPROCESSING = "disable-frontend-multiprocessing"
    NO_ENABLE_CHUNKED_PREFILL = "no-enable-chunked-prefill"
    ENFORCE_EAGER = "enforce-eager"

    @classmethod
    def dict(cls):
        """Map environment variables to VLLM server arguments."""
        class_vars = {}
        for key, value in vars(VLLMArgs).items():
            if not callable(value) and isinstance(value, str) and not key.startswith("__"):
                class_vars[key] = value
        return class_vars

    @classmethod
    def reverse_dict(cls):
        """Map VLLM server arguments to their environment variables."""
        reverse_class_vars = {}
        for key, value in vars(VLLMArgs).items():
            if not callable(value) and isinstance(value, str) and not key.startswith("__"):
                reverse_class_vars[value] = key
        return reverse_class_vars


class VLLMKwargs:
    """Vllm server key word arguments."""

    HOST = "host"
    PORT = "port"
    MODEL = "model"
    TOKENIZER = "tokenizer"
    REVISION = "revision"
    CODE_REVISION = "code-revision"
    TOKENIZER_REVISION = "tokenizer-revision"
    TOKENIZER_MODE = "tokenizer-mode"
    DOWNLOAD_DIR = "download-dir"
    LOAD_FORMAT = "load-format"
    DTYPE = "dtype"
    KV_CACHE_DTYPE = "kv-cache-dtype"
    QUANTIZATION_PARAM_PATH = "quantization-param-path"
    GUIDED_DECODING_BACKEND = "guided-decoding-backend"
    MAX_MODEL_LEN = "max-model-len"
    DISTRIBUTED_EXECUTOR_BACKEND = "distributed-executor-backend"
    PIPELINE_PARALLEL_SIZE = "pipeline-parallel-size"
    TENSOR_PARALLEL_SIZE = "tensor-parallel-size"
    MAX_PARALLEL_LOADING_WORKERS = "max-parallel-loading-workers"
    BLOCK_SIZE = "block-size"
    NUM_LOOKAHEAD_SLOTS = "num-lookahead-slots"
    SEED = "seed"
    SWAP_SPACE = "swap-space"
    GPU_MEMORY_UTILIZATION = "gpu-memory-utilization"
    NUM_GPU_BLOCKS_OVERRIDE = "num-gpu-blocks-override"
    MAX_NUM_BATCHED_TOKENS = "max-num-batched-tokens"
    MAX_NUM_SEQS = "max-num-seqs"
    MAX_LOGPROBS = "max-logprobs"
    MAX_PADDINGS = "max-paddings"
    QUANTIZATION = "quantization"
    ROPE_SCALING = "rope-scaling"
    MAX_LOG_LEN = "max-log-len"
    MAX_CONTEXT_LEN_TO_CAPTURE = "max-context-len-to-capture"
    MAX_SEQ_LEN_TO_CAPTURE = "max-seq-len-to-capture"
    TOKENIZER_POOL_SIZE = "tokenizer-pool-size"
    TOKENIZER_POOL_TYPE = "tokenizer-pool-type"
    TOKENIZER_POOL_EXTRA_CONFIG = "tokenizer-pool-extra-config"
    MAX_LORAS = "max-loras"
    MAX_LORA_RANK = "max-lora-rank"
    LORA_EXTRA_VOCAB_SIZE = "lora-extra-vocab-size"
    LORA_DTYPE = "lora-dtype"
    LONG_LORA_SCALING_FACTORS = "long-lora-scaling-factors"
    MAX_CPU_LORAS = "max-cpu-loras"
    DEVICE = "device"
    IMAGE_INPUT_TYPE = "image-input-type"
    IMAGE_TOKEN_ID = "image-token-id"
    IMAGE_INPUT_SHAPE = "image-input-shape"
    IMAGE_FEATURE_SIZE = "image-feature-size"
    IMAGE_OPENAI = "image-openai"
    SCHEDULER_DELAY_FACTOR = "scheduler-delay-factor"
    SPECULATIVE_MODEL = "speculative-model"
    NUM_SPECULATIVE_TOKENS = "num-speculative-tokens"
    SPECULATIVE_MAX_MODEL_LEN = "speculative-max-model-len"
    SPECULATIVE_DISABLE_BY_BATCH_SIZE = "speculative-disable-by-batch-size"
    NGRAM_PROMPT_LOOKUP_MAX = "ngram-prompt-lookup-max"
    NGRAM_PROMPT_LOOKUP_MIN = "ngram-prompt-lookup-min"
    MODEL_LOADER_EXTRA_CONFIG = "model-loader-extra-config"
    SERVED_MODEL_NAME = "served-model-name"
    LORA_MODULES = "lora-modules"
    LIMIT_MM_PER_PROMPT = "limit-mm-per-prompt"
    COMPILATION_CONFIG = "compilation-config"

    @classmethod
    def dict(cls):
        """Map environment variables to VLLM server key word arguments."""
        class_vars = {}
        for key, value in vars(VLLMKwargs).items():
            if not callable(value) and isinstance(value, str) and not key.startswith("__"):
                class_vars[key] = value
        return class_vars

    @classmethod
    def vllm_kwargs_with_list_input(cls):
        """Return vllm kwargs which supports list input."""
        VLLM_KWARGS_WITH_LIST_INPUT = [VLLMKwargs.LORA_MODULES]
        return VLLM_KWARGS_WITH_LIST_INPUT


class DataTypes:
    """Data type for model weights and activations."""

    AUTO = "auto"
    BFLOAT16 = "bfloat16"
    FLOAT = "float"
    FLOAT16 = "float16"
    FLOAT32 = "float32"
    HALF = "half"
