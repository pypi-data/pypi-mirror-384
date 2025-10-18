import math
import os
from functools import wraps
from typing import Optional, Tuple

import torch

BASE_GPU_MEMORY_BYTES = 40 * 1024**3  # 40GB reference card


def with_env_var(var_name, value):
    """
    Decorator to set an environment variable for the duration of a function call.
    
    Args:
        var_name (str): The name of the environment variable to set.
        value (str): The value to set the environment variable to.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            original_value = os.environ.get(var_name)
            os.environ[var_name] = value
            try:
                return func(*args, **kwargs)
            finally:
                if original_value is None:
                    del os.environ[var_name]
                else:
                    os.environ[var_name] = original_value
        return wrapper
    return decorator


def get_gpu_memory_bytes(device=None) -> Tuple[Optional[int], Optional[int]]:
    """
    Return available and total GPU memory (in bytes) for the requested device.
    """
    if not torch.cuda.is_available():
        return None, None

    if device is None:
        device = torch.cuda.current_device()

    device = torch.device(device)
    if device.type != 'cuda':
        return None, None

    with torch.cuda.device(device):
        try:
            free_bytes, total_bytes = torch.cuda.mem_get_info()
        except RuntimeError:
            total_bytes = torch.cuda.get_device_properties(device).total_memory
            allocated = torch.cuda.memory_allocated()
            reserved = torch.cuda.memory_reserved()
            free_bytes = total_bytes - max(allocated, reserved)

    # guard against negative or zero values
    free_bytes = max(int(free_bytes), 0)
    total_bytes = max(int(total_bytes), 0)
    return free_bytes, total_bytes


def memory_scaling_factor(device=None, *, quadratic=False, base_memory_bytes=BASE_GPU_MEMORY_BYTES) -> float:
    """
    Compute a scaling factor relative to a 40GB GPU.
    
    Parameters
    ----------
    device : Union[str, torch.device, int], optional
        Target CUDA device. Defaults to the current device.
    quadratic : bool, default=False
        If True, return sqrt(memory_ratio) to account for quadratic scaling.
    base_memory_bytes : int, default=40GB
        Reference memory used for ratio calculation.
    """
    if base_memory_bytes <= 0:
        return 1.0

    free_bytes, _ = get_gpu_memory_bytes(device)
    if free_bytes is None or free_bytes == 0:
        return 1.0

    memory_ratio = max(free_bytes / base_memory_bytes, 1e-3)
    if quadratic:
        return math.sqrt(memory_ratio)
    return memory_ratio
