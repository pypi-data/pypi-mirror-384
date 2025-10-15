# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""This module provides a decorator to log the execution time of functions."""
import os
import time
import io
import base64
import requests

import torch

from llm.optimized.inference.logging_config import configure_logger
from llm.optimized.inference.constants import VLLMArgs, VLLMKwargs
from PIL.Image import Image

logger = configure_logger(__name__)


def log_execution_time(func):
    """Decorate a function to log the execution time.

    :param func: The function to be decorated.
    :return: The decorated function.
    """

    def wrapper(*args, **kwargs):
        """Calculate and log the execution time.

        :param args: Positional arguments for the decorated function.
        :param kwargs: Keyword arguments for the decorated function.
        :return: The result of the decorated function.
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        if func.__name__ == "wait_until_server_healthy" and os.environ.get("LOGGING_WORKER_ID", "") == str(
            os.getpid(),
        ):
            logger.info(
                f"Function {func.__name__} took {elapsed_time:.4f} seconds to execute.",
            )
        return result

    return wrapper


def box_logger(message: str):
    """Log a message, but in a box."""
    row = len(message)
    h = "".join(["+"] + ["-" * row] + ["+"])
    result = "\n" + h + "\n" + message + "\n" + h
    logger.info(result)


def map_env_vars_to_vllm_server_kwargs() -> dict:
    """Map environment variables to VLLM server key word arguments."""
    env_to_cli_map = VLLMKwargs.dict()
    cli_args = {}
    for env_var, cli_arg in env_to_cli_map.items():
        if env_var in os.environ:
            cli_args[cli_arg] = os.environ[env_var]

    box_logger(f"vLLM server key word arguments: {cli_args}")

    return cli_args


def map_env_vars_to_vllm_server_args() -> list:
    """Map environment variables to VLLM server arguments."""
    env_to_cli_map = VLLMArgs.dict()
    cli_args = []
    for env_var, cli_arg in env_to_cli_map.items():
        value = os.getenv(env_var, "False")
        if eval(value):
            cli_args.append(cli_arg)

    box_logger(f"vLLM server arguments: {cli_args}")

    return cli_args


def image_to_base64(img: Image, format: str) -> str:
    """
    Convert image into Base64 encoded string.

    :param img: image object
    :type img: PIL.Image.Image
    :param format: image format
    :type format: str
    :return: base64 encoded string
    :rtype: str
    """
    buffered = io.BytesIO()
    img.save(buffered, format=format)
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str


def convert_image_to_bytes(image: str) -> bytes:
    """Convert image into bytes.

    :param image: The Base64 encoded string to be decoded or http url.
    :type image: str
    :return: The decoded bytes object.
    :rtype: bytes
    """
    try:
        if image.startswith("http://") or image.startswith("https://"):
            try:
                image = requests.get(image, stream=True)
                image = image.content
            except Exception as ex:
                raise Exception(
                    f"Failed to download the image from the URL. {str(ex)}."
                    "Alternatively, use images in base64 format."
                )
        else:
            image = base64.b64decode(image)
    except Exception as ex:
        raise ValueError(
            f"Image should be either URL or in base64 format. URLs must start with `http://` or `https://`. {str(ex)}"
        )
    return image


def get_gpu_device_capability() -> float:
    """
    Get the GPU device capability version.

    :return: GPU device capability version
    :rtype: float
    """
    properties = torch.cuda.get_device_properties(0)
    return float(f"{properties.major}.{properties.minor}")
