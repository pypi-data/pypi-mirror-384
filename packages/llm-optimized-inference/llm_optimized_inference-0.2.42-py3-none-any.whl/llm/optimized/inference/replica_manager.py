# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""This class provides model replication and load balancing functionality."""
import os
import random
import tempfile
import time
import torch
from concurrent.futures import ThreadPoolExecutor
import traceback
from copy import deepcopy
from dataclasses import dataclass
from typing import List

from llm.optimized.inference.configs import EngineConfig, TaskConfig
from llm.optimized.inference.constants import VLLMSpecialModels
from llm.optimized.inference.engine import BaseEngine
from llm.optimized.inference.logging_config import configure_logger
from llm.optimized.inference.model_utils import get_model_size_in_gb, verify_model_fits_in_gpu


logger = configure_logger(__name__)
ML_CONFIG_PATH = "mlflow_model_folder/ml_configs"


def get_engine(engine_config: EngineConfig, task_config: TaskConfig) -> BaseEngine:
    """Return the appropriate engine based on the engine name."""
    engine_name = engine_config.engine_name
    if engine_name == "hf":
        from llm.optimized.inference.engine.hf_engine import HfEngine

        return HfEngine(engine_config, task_config)
    elif engine_name == "vllm":
        from llm.optimized.inference.engine.vllm_engine import VLLMEngine

        return VLLMEngine(engine_config, task_config)
    elif engine_name == "mii":
        from llm.optimized.inference.engine.mii_engine_v2 import MiiEngineV2

        return MiiEngineV2(engine_config, task_config)
    elif engine_name == "mii-v1":
        from llm.optimized.inference.engine.mii_engine import MiiEngine

        return MiiEngine(engine_config, task_config)
    else:
        raise ValueError("Invalid engine name.")


@dataclass
class ReplicaManagerConfig:
    """Data class for storing the configuration of a ReplicaManager."""

    engine_config: EngineConfig  # homogeneous config for all replicas
    task_config: TaskConfig
    num_replicas: int
    gpu_ids: str = ""

    def __post_init__(self):
        """Initialize the ReplicaManagerConfig."""
        if self.gpu_ids == "":
            self.gpu_ids = self._get_cuda_visible_devices()

    @staticmethod
    def _get_cuda_visible_devices():
        """Get the CUDA_VISIBLE_DEVICES environment variable or set it to all available GPUs.

        Returns a comma-separated string of GPU IDs, e.g. "0,1,2,3"
        """
        gpu_ids = os.environ.get("CUDA_VISIBLE_DEVICES", None)
        if gpu_ids is None:
            gpu_ids = ",".join(map(str, range(torch.cuda.device_count()))) if torch.cuda.is_available() else ""
        return gpu_ids


class ReplicaManager:
    """Class for managing replicas of a model."""

    def __init__(self, replica_config: ReplicaManagerConfig):
        """Initialize the ReplicaManager."""
        self._replica_config = replica_config
        self._engine_config = self._replica_config.engine_config
        self.is_hf = False
        if self._engine_config.engine_name == "hf":
            self.is_hf = True
        self._task_config = self._replica_config.task_config

        self.engine_replicas = []  # type: List[BaseEngine]
        self._replica_index = 0  # index of the next available replica
        self._tensor_parallel = self._replica_config.engine_config.tensor_parallel

        self._set_defaults()

    def initialize(self):
        """Initialize the ReplicaManager by creating engine replicas."""
        num_replicas = self._replica_config.num_replicas
        # create engine replicas
        for idx in list(range(num_replicas)):
            engine_config = deepcopy(self._replica_config.engine_config)
            engine_config.tensor_parallel = self._tensor_parallel
            engine_config.num_replicas = num_replicas
            engine_config.port = self._replica_config.engine_config.port + idx
            engine_replica = get_engine(engine_config, self._task_config)
            self.engine_replicas.append(engine_replica)

        """
        This block of code is used to handle the loading of the model in a multi-process environment.
        A flag file at "/tmp/model_loaded_flag.txt" is used as a lock to ensure that the model is loaded only once.
        If the flag file exists, it means the model is already being loaded by another worker.
        If the flag file does not exist, the current worker creates the flag file and loads the model.
        If the flag file creation fails due to FileExistsError, it means another worker is currently loading
        the model.
        The current worker then waits for the model to finish loading.
        After the model has been loaded and the client has been initialized, the flag file is removed,
        acting as releasing the lock.
        """
        flag_file_path = os.path.join(tempfile.gettempdir(), "model_loaded_flag.txt")
        process_is_loading_model = False

        # wait a random amount of time between 1-5 seconds (in float), to avoid all workers trying to acquire
        # the lock at the same time
        time.sleep(random.uniform(0, 2))

        if os.path.exists(flag_file_path):
            logger.info(
                f"PID[{os.getpid()}] Model already being loaded by another worker.",
            )
            # wait for all replicas to finish loading the model
            while os.path.exists(flag_file_path):
                logger.info(f"Waiting for model to finish loading. Current worker pid: {os.getpid()}")
                time.sleep(5)
            for engine in self.engine_replicas:
                engine.init_client()
        else:
            try:
                with open(flag_file_path, "x"):
                    logger.info(
                        f"Lock acquired by worker with pid: {os.getpid()}. Loading model. \
Using tensor parallel of {self._tensor_parallel} GPUs per replica.",
                    )
                    process_is_loading_model = True
                    logger.handlers[0].flush()
                    os.environ["LOGGING_WORKER_ID"] = str(os.getpid())

                    if self._engine_config.engine_name == "hf":
                        # Synchronously create model instances
                        logger.info("Launching Replicas synchronously")
                        for idx in range(num_replicas):
                            logger.info(f"Launching Replica: {idx}")
                            self.engine_replicas[idx] = self._launch_single_replica(idx)
                    else:
                        # Start replicas in parallel using ProcessPoolExecutor
                        with ThreadPoolExecutor() as executor:
                            self.engine_replicas = list(
                                executor.map(
                                    self._launch_single_replica,
                                    range(num_replicas),
                                )
                            )
            except FileExistsError:
                logger.info(
                    f"Model already being loaded by another worker. Waiting for model to finish loading. "
                    f"Current worker pid: {os.getpid()}",
                )

        if process_is_loading_model:
            # Load the model and print GPU information
            logger.info("###### GPU INFO ######")
            logger.info(os.system("nvidia-smi"))
            logger.info("###### GPU INFO ######")

            if os.path.exists(flag_file_path):
                os.remove(flag_file_path)

        if os.environ.get("LOGGING_WORKER_ID", "") == str(os.getpid()):
            print(f"Initialized {self._replica_config.num_replicas} replicas.")
            print(f"Server URIs: {[engine.server_url for engine in self.engine_replicas]}")

    def _launch_single_replica(self, replica_idx):
        """Launch a single replica."""
        engine_replica = self.engine_replicas[replica_idx]
        gpu_ids_list = [int(gpu_id.strip()) for gpu_id in self._replica_config.gpu_ids.split(",")]

        local_env = os.environ.copy()
        replica_gpu_ids = self._get_gpu_ids_for_replica(replica_idx, gpu_ids_list)
        cuda_visible_devices = ",".join(map(str, replica_gpu_ids))
        logger.debug(f"Setting CUDA_VISIBLE_DEVICES to {cuda_visible_devices} for replica {replica_idx + 1}")
        local_env["CUDA_VISIBLE_DEVICES"] = cuda_visible_devices

        try:
            logger.info(
                f"Starting replica {replica_idx + 1} with GPUs {cuda_visible_devices} "
                f"for engine: {engine_replica.engine_config.engine_name}",
            )
            engine_replica.load_model(env=local_env)
            engine_replica.init_client()
        except Exception as e:
            logger.error(f"Failed to start replica {replica_idx + 1} with GPUs {cuda_visible_devices}: {e}")
            traceback.print_exc()
        return engine_replica

    def _get_gpu_ids_for_replica(self, replica_idx: int, gpu_ids_list: List[int]) -> List[int]:
        """Get the GPU IDs for a specific replica."""
        # By default, use all available GPUs
        if self._tensor_parallel in ["", None]:
            replica_gpu_ids = gpu_ids_list
        else:
            # Determine the GPU IDs to use for this replica.
            start_gpu_idx = replica_idx * self._tensor_parallel
            end_gpu_idx = start_gpu_idx + self._tensor_parallel
            replica_gpu_ids = gpu_ids_list[start_gpu_idx:end_gpu_idx]
        return replica_gpu_ids

    def get_replica(self) -> BaseEngine:
        """Return the next available replica based on round-robin."""
        replica = self.engine_replicas[self._replica_index]
        self._replica_index = (self._replica_index + 1) % len(self.engine_replicas)  # Next replica index
        logger.info(
            f"Returning replica {self._replica_index} with server URI {replica.server_url} as the next "
            f"available replica.",
        )
        return replica

    def _get_tensor_parallel(self, device_count):
        """Get the tensor parallel configuration for each replica."""
        # evenly divide the available GPUs among the replicas
        res = max(device_count // self._replica_config.num_replicas, 1)
        logger.info(f"Using tensor parallel of {res} GPUs per replica.")
        return res

    def _set_defaults(self):
        """Do some sanity checks and set default values for the replica config and tensor parallel."""
        gpu_ids_list = [int(gpu_id.strip()) for gpu_id in self._replica_config.gpu_ids.split(",")]
        device_count = len(gpu_ids_list)

        kwargs = {}
        if self._engine_config.vllm_config:
            kwargs = self._engine_config.vllm_config.get("vllm_kwargs", {})

        # TODO: Remove this once all models adopt inference_config.json
        else:
            model_config = self._engine_config.model_config or {}
            ml_model_info = self._engine_config.ml_model_info or {}
            model = model_config.get("model_type", "")
            kwargs = VLLMSpecialModels.get_kwargs(model, ml_model_info.get("model_id", None))

        tensor_size = kwargs.get("tensor-parallel-size", None)
        quantization = "quantization" in kwargs

        if self._replica_config.num_replicas >= 1:
            if self._tensor_parallel in [None, ""]:
                raise ValueError(
                    "Tensor parallel must be specified when using multiple replicas. "
                    "Set it using environment variable 'TENSOR_PARALLEL'.",
                )
            total_gpus_needed = self._replica_config.num_replicas * self._tensor_parallel

            # User misconfigured the settings, throw error
            if total_gpus_needed > device_count:
                raise ValueError(
                    f"Insufficient GPUs: Need {total_gpus_needed} but only {device_count} are available. "
                    f"Reduce NUM_REPLICAS or TENSOR_PARALLEL to fit within the available GPUs.",
                )

        else:
            self._replica_config.num_replicas = 1
            if not self._tensor_parallel:
                self._tensor_parallel = (
                    tensor_size
                    if tensor_size
                    else self._get_tensor_parallel(device_count)
                )

            if self._tensor_parallel > device_count:
                logger.warning(f"Tensor parallel {self._tensor_parallel} greater than device count {device_count}.")
                self._tensor_parallel = self._get_tensor_parallel(device_count)
            self._replica_config.num_replicas = device_count // self._tensor_parallel

        logger.info(f"Setting tensor parallel to {self._tensor_parallel} and num replicas to "
                    f"{self._replica_config.num_replicas}")

        model_size = get_model_size_in_gb(self._engine_config.model_id)
        verify_model_fits_in_gpu(model_size, self._tensor_parallel, quantization=quantization)


if __name__ == "__main__":
    engine_config = EngineConfig(
        engine_name="vllm",
        model_id="/data/Llama-2-7b-chat/mlflow_model_folder/data/model/",
        tensor_parallel=1,
    )

    replica_config = ReplicaManagerConfig(
        engine_config=engine_config,
        task_config=TaskConfig(),
        num_replicas=4,
    )

    replica_manager = ReplicaManager(replica_config)
    replica_manager.initialize()

    print("Initialized replicas.")

    prompt = "The meaning of life is"
    max_new_tokens = 500

    for i in range(replica_config.num_replicas):
        engine_replica = replica_manager.get_replica()
        print(f"Replica {i + 1} server URI: {engine_replica.server_url}")
        print(engine_replica.generate([prompt], {"max_new_tokens": max_new_tokens}))
        print()

    while True:
        time.sleep(1)
