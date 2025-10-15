# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Run script to infer."""
# flake8: noqa

import dataclasses
import json
import os
import shutil

import numpy as np
import pandas as pd
import torch
import yaml
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions, AnalyzeImageOptions, ImageData
from azure.core.credentials import AzureKeyCredential
from azure.core.pipeline.policies import HeadersPolicy
from azureml.ai.monitoring import Collector
from llm.optimized.inference.constants import EngineName, SupportedTask, TaskType, ALL_TASKS, VLLMSupportedModels, MIISupportedModels
from llm.optimized.inference.model_config_factory import ModelConfigFactory
from llm.optimized.inference.fm_score import FMScore
from llm.optimized.inference.logging_config import configure_logger
from llm.optimized.inference.managed_inference import MIRPayload
from mlflow.pyfunc.scoring_server import _get_jsonable_obj
from llm.optimized.inference.utils import box_logger, map_env_vars_to_vllm_server_args
from llm.optimized.inference.model_utils import build_configs_from_model, get_generator_params

logger = configure_logger(__name__)

# AACS
g_aacs_threshold = int(os.environ.get("CONTENT_SAFETY_THRESHOLD", 2))
g_aacs_client = None

# default values
DEVICE_COUNT = torch.cuda.device_count()
MLMODEL_PATH = "mlflow_model_folder/MLmodel"
DEPRECATED_MLFLOW_MODEL_PATH = "mlflow_model_folder/data/model"
DEPRECATED_MLFLOW_CONFIG_PATH = "mlflow_model_folder/data/config"
DEPRECATED_MLFLOW_TOKENIZER_PATH = "mlflow_model_folder/data/tokenizer"
DEFAULT_MLFLOW_MODEL_PATH = "mlflow_model_folder/model"
DEFAULT_TOKENIZER_PATH = "mlflow_model_folder/components/tokenizer"
task_type = SupportedTask.TEXT_GENERATION
g_fmscorer: FMScore = None
g_model_signature = None

# # metrics tracking
g_collector = Collector(
    name="inference_metrics",
    on_error=lambda e: logger.info("ex:{}".format(e)),
)


# region AACS
class CsChunkingUtils:
    """Cs chunking utils."""

    def __init__(self, chunking_n=1000, delimiter="."):
        """Init function."""
        self.delimiter = delimiter
        self.chunking_n = chunking_n

    def chunkstring(self, string, length):
        """Chunk strings in a given length."""
        return (string[0 + i : length + i] for i in range(0, len(string), length))

    def split_by(self, input):
        """Split the input."""
        max_n = self.chunking_n
        split = [e + self.delimiter for e in input.split(self.delimiter) if e]
        ret = []
        buffer = ""

        for i in split:
            # if a single element > max_n, chunk by max_n
            if len(i) > max_n:
                ret.append(buffer)
                ret.extend(list(self.chunkstring(i, max_n)))
                buffer = ""
                continue
            if len(buffer) + len(i) <= max_n:
                buffer = buffer + i
            else:
                ret.append(buffer)
                buffer = i

        if len(buffer) > 0:
            ret.append(buffer)
        return ret


def analyze_response(response):
    """Analyze response."""
    severity = 0

    if response.hate_result is not None:
        logger.info("Hate severity: {}".format(response.hate_result.severity))
        severity = max(severity, response.hate_result.severity)
    if response.self_harm_result is not None:
        logger.info("SelfHarm severity: {}".format(response.self_harm_result.severity))
        severity = max(severity, response.self_harm_result.severity)
    if response.sexual_result is not None:
        logger.info("Sexual severity: {}".format(response.sexual_result.severity))
        severity = max(severity, response.sexual_result.severity)
    if response.violence_result is not None:
        logger.info("Violence severity: {}".format(response.violence_result.severity))
        severity = max(severity, response.violence_result.severity)

    return severity


def analyze_text(text):
    """Analyze text."""
    global g_aacs_client
    # Chunk text
    logger.info("Analyzing ...")
    if (not text) or (not text.strip()):
        return 0
    chunking_utils = CsChunkingUtils(chunking_n=1000, delimiter=".")
    split_text = chunking_utils.split_by(text)

    result = [analyze_response(g_aacs_client.analyze_text(AnalyzeTextOptions(text=i))) for i in split_text]
    severity = max(result)
    logger.info(f"Analyzed, severity {severity}")

    return severity


def analyze_image(image_in_byte64: str) -> int:
    """Analyze image severity using azure content safety service.

    :param image_in_byte64: image in base64 format
    :type image_in_byte64: str
    :return: maximum severity of all categories
    :rtype: int
    """
    print("Analyzing image...")
    if image_in_byte64 is None:
        return 0
    request = AnalyzeImageOptions(image=ImageData(content=image_in_byte64))
    safety_response = g_aacs_client.analyze_image(request)
    severity = analyze_response(safety_response)
    print(f"Image Analyzed, severity {severity}")
    return severity


def _check_data_type_from_model_signature(key: str) -> str:
    """Check key data type from model signature.

    :param key: key of data (to analyze by AACS) in model input or output
    :type key: str
    :return: data type of key from model signature else return "str"
    :rtype: str
    """
    if g_model_signature is None or key is None:
        return "str"
    input_schema = g_model_signature["inputs"]
    output_schema = g_model_signature["outputs"]

    def _get_type(schema):
        if type(schema) == str:
            schema = json.loads(schema)

        for item in schema:
            if item["name"] == key:
                return item["type"]
        return None

    return _get_type(input_schema) or _get_type(output_schema) or "str"


def iterate(obj, current_key=None):
    """Iterate through obj and check content severity."""
    if isinstance(obj, dict):
        severity = 0
        for key, value in obj.items():
            obj[key], value_severity = iterate(value, current_key=key)
            severity = max(severity, value_severity)
        return obj, severity
    elif isinstance(obj, list) or isinstance(obj, np.ndarray):
        severity = 0
        for idx in range(len(obj)):
            obj[idx], value_severity = iterate(obj[idx], current_key=current_key)
            severity = max(severity, value_severity)
        return obj, severity
    elif isinstance(obj, pd.DataFrame):
        severity = 0
        columns = list(obj.columns)
        for i in range(obj.shape[0]):  # iterate over rows
            for j in range(obj.shape[1]):  # iterate over columns
                obj.at[i, j], value_severity = iterate(obj.at[i, j], current_key=columns[j])
                severity = max(severity, value_severity)
        return obj, severity
    elif isinstance(obj, str):
        if current_key and _check_data_type_from_model_signature(current_key) == "binary":
            severity = analyze_image(obj)
        else:
            severity = analyze_text(obj)
        if severity > g_aacs_threshold:
            return "", severity
        else:
            return obj, severity
    else:
        return obj, 0


def get_safe_response(result):
    """Check if response is safe."""
    global g_aacs_client
    logger.info("Analyzing response...")
    jsonable_result = _get_jsonable_obj(result, pandas_orient="records")
    if not g_aacs_client:
        return jsonable_result

    result, severity = iterate(jsonable_result)
    logger.info(f"Response analyzed, severity {severity}")
    return result


def get_safe_input(input_data):
    """Check if input is safe."""
    global g_aacs_client
    if not g_aacs_client:
        return input_data, 0
    logger.info("Analyzing input...")
    result, severity = iterate(input_data)
    logger.info(f"Input analyzed, severity {severity}")
    return result, severity


def get_aacs_access_key():
    """Get aacs access key."""
    key = os.environ.get("CONTENT_SAFETY_KEY")

    if key:
        return key

    uai_client_id = os.environ.get("UAI_CLIENT_ID")
    if not uai_client_id:
        raise RuntimeError(
            "Cannot get AACS access key, both UAI_CLIENT_ID and " "CONTENT_SAFETY_KEY are not set, exiting...",
        )

    subscription_id = os.environ.get("SUBSCRIPTION_ID")
    resource_group_name = os.environ.get("RESOURCE_GROUP_NAME")
    aacs_account_name = os.environ.get("CONTENT_SAFETY_ACCOUNT_NAME")
    from azure.identity import ManagedIdentityCredential
    from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient

    credential = ManagedIdentityCredential(client_id=uai_client_id)
    cs_client = CognitiveServicesManagementClient(credential, subscription_id)
    key = cs_client.accounts.list_keys(
        resource_group_name=resource_group_name,
        account_name=aacs_account_name,
    ).key1

    return key


# endregion


def _init_cuda_visible_devices():
    import torch

    if "CUDA_VISIBLE_DEVICES" in os.environ:
        return

    if "NVIDIA_VISIBLE_DEVICES" in os.environ and os.environ["NVIDIA_VISIBLE_DEVICES"] != "all":
        # map the gpu ids to integers
        gpu_ids = os.environ["NVIDIA_VISIBLE_DEVICES"].split(",")
        gpu_ids = [str(i) for i in range(len(gpu_ids)) if gpu_ids[i] != "-1"]
    elif torch.cuda.is_available():
        gpu_ids = [str(i) for i in range(torch.cuda.device_count())]
    else:
        # if no GPU is available, don't set anything
        return
    os.environ["CUDA_VISIBLE_DEVICES"] = ",".join(gpu_ids)



def init():
    """Initialize text-generation-inference server and client."""
    global g_fmscorer
    global task_type
    global g_aacs_client
    global g_model_signature

    AACS_error = None
    try:
        endpoint = os.environ.get("CONTENT_SAFETY_ENDPOINT", None)
        key = get_aacs_access_key()

        if not endpoint:
            raise Exception("CONTENT_SAFETY_ENDPOINT env not set for AACS.")
        if not key:
            raise Exception("CONTENT_SAFETY_KEY env not set for AACS.")

        # Create a Content Safety client
        headers_policy = HeadersPolicy()
        headers_policy.add_header("ms-azure-ai-sender", "fm-optimized-inference")
        g_aacs_client = ContentSafetyClient(
            endpoint,
            AzureKeyCredential(key),
            headers_policy=headers_policy,
        )
    except Exception as e:
        AACS_error = e
    try:
        if os.path.exists(os.path.join(os.getenv("AZUREML_MODEL_DIR", ""), DEFAULT_MLFLOW_MODEL_PATH)):
            model_path = os.path.join(
                os.getenv("AZUREML_MODEL_DIR", ""),
                DEFAULT_MLFLOW_MODEL_PATH,
            )
            config_path = os.path.join(model_path, "config.json")
            tokenizer_path = os.path.join(
                os.getenv("AZUREML_MODEL_DIR", ""), DEFAULT_TOKENIZER_PATH
            )
        else:
            model_path = os.path.join(os.getenv("AZUREML_MODEL_DIR", ""), DEPRECATED_MLFLOW_MODEL_PATH)
            config_path = os.path.join(
                os.getenv("AZUREML_MODEL_DIR", ""), DEPRECATED_MLFLOW_CONFIG_PATH, "config.json"
            )
            tokenizer_path = os.path.join(
                os.getenv("AZUREML_MODEL_DIR", ""), DEPRECATED_MLFLOW_TOKENIZER_PATH
            )
            

        _init_cuda_visible_devices()

        abs_mlmodel_path = os.path.join(
            os.getenv("AZUREML_MODEL_DIR", ""),
            MLMODEL_PATH,
        )
        mlmodel = {}
        if abs_mlmodel_path and os.path.exists(abs_mlmodel_path):
            with open(abs_mlmodel_path) as f:
                mlmodel = yaml.safe_load(f)

        if mlmodel:
            g_model_signature = mlmodel.get("signature", None)
        engine_config, task_config, default_generator_configs, task_type = build_configs_from_model(
            mlmodel,
            model_path,
            config_path,
            tokenizer_path
        )

        config = {
            "engine": engine_config,
            "task": task_config,
        }

        g_fmscorer = FMScore(config)
        g_fmscorer.init()
        if os.environ.get("LOGGING_WORKER_ID", "") == str(os.getpid()):
            for k, v in os.environ.items():
                logger.info(f"env: {k} = {v}")
            logger.info(
                f"updated default_generator_configs: " f"{default_generator_configs}",
            )
            if AACS_error:
                logger.warning(f"AACS was not configured. Content moderation bypassed in setup. Error {AACS_error}")

    except Exception as e:
        raise Exception(f"Error in creating client or server: {e}") from e


def run(data):
    """Run for inference data provided."""
    global g_fmscorer
    global task_type

    try:
        data, severity = get_safe_input(data)
        if severity > g_aacs_threshold:
            logger.warning(
                f"Input severity ({severity}) greater than aacs threshold " f"({g_aacs_threshold}).",
            )
            return {}

        data = json.loads(data)
        data.update({"task_type": task_type})

        payload = MIRPayload.from_dict(data)
        payload.update_params(get_generator_params(payload.params))
        logger.info(
            f"Processing new request with parameters: {payload.params}",
        )

        results = {}
        inference_results = None
        if task_type == SupportedTask.CHAT_COMPLETION:
            payload.convert_query_to_list()
            inference_results = g_fmscorer.run(payload)
            outputs = {str(i): res.response for i, res in enumerate(inference_results)}
            results = {
                "output": f"{outputs['0']}",
            }  # outputs will only have one key for chat-completion
        elif task_type == SupportedTask.TEXT_TO_IMAGE:
            inference_results = g_fmscorer.run(payload)
            results = [dataclasses.asdict(res.response) for res in inference_results]
        else:
            assert task_type == SupportedTask.TEXT_GENERATION and isinstance(
                payload.query,
                list,
            ), "query should be a list for text-generation"
            inference_results = g_fmscorer.run(payload)
            # output format: [output1, output2, ...]
            results = [res.response for res in inference_results]

        for inference_result in inference_results:
            inference_result.print_results()
        all_logged_results = f""" ### Inference Results ###\n \
Total Generation Time: {inference_results[0].inference_time_ms}\n \
Throughput (prompt/sec): {len(inference_results) / (inference_results[0].inference_time_ms / 1000):.2f}"""
        box_logger(all_logged_results)

        stats_dict = [vars(result) for result in inference_results]
        g_collector.collect(stats_dict)
        return get_safe_response(results)

    except Exception as e:
        logger.exception(e)
        return json.dumps({"error": "Error in processing request", "exception": str(e)})


if __name__ == "__main__":
    logger.info(init())
    assert task_type is not None

    valid_inputs = {
        "text-generation": [
            {
                "input_data": ["the meaning of life is"],
                "params": {"max_new_tokens": 256, "do_sample": True},
            },
            {
                "input_data": [
                    "The recipe of a good movie is",
                    "Quantum physics is",
                    "the meaning of life is",
                ],
                "params": {
                    "max_new_tokens": 256,
                    "do_sample": True,
                    # "_batch_size": 32,
                },
            },
        ],
        "chat-completion": [
            {
                "input_data": {
                    "input_string": [
                        {
                            "role": "user",
                            "content": "What is the tallest building in the world?",
                        },
                        {
                            "role": "assistant",
                            "content": "As of 2021, the Burj Khalifa in Dubai, United Arab Emirates is the tallest building in the world, standing at a height of 828 meters (2,722 feet). It was completed in 2010 and has 163 floors. The Burj Khalifa is not only the tallest building in the world but also holds several other records, such as the highest occupied floor, highest outdoor observation deck, elevator with the longest travel distance, and the tallest freestanding structure in the world.",
                        },
                        {"role": "user", "content": "and in Africa?"},
                        {
                            "role": "assistant",
                            "content": "In Africa, the tallest building is the Carlton Centre, located in Johannesburg, South Africa. It stands at a height of 50 floors and 223 meters (730 feet). The CarltonDefault Centre was completed in 1973 and was the tallest building in Africa for many years until the construction of the Leonardo, a 55-story skyscraper in Sandton, Johannesburg, which was completed in 2019 and stands at a height of 230 meters (755 feet). Other notable tall buildings in Africa include the Ponte City Apartments in Johannesburg, the John Hancock Center in Lagos, Nigeria, and the Alpha II Building in Abidjan, Ivory Coast",
                        },
                        {"role": "user", "content": "and in Europe?"},
                    ],
                    "parameters": {
                        "temperature": 0.9,
                        "top_p": 0.6,
                        "do_sample": True,
                        "max_new_tokens": 100,
                    },
                },
            },
        ],
        TaskType.TEXT_TO_IMAGE: [
            {
                "input_data": {
                        "columns": ["prompt"],
                        "data": ["Photograph of a dog with severed leg and bleeding profusely from deep laceration to the lower extremities, exposing tissues and nerve.", "lion holding hunted deer in grass fields"]
                    }
            }
        ]
    }

    for sample_ip in valid_inputs[task_type]:
        logger.info(run(json.dumps(sample_ip)))
