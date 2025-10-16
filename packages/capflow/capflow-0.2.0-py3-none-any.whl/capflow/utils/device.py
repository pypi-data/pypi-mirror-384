"""Device selection utilities for cross-platform compatibility."""

import torch
import logging

logger = logging.getLogger(__name__)


def get_optimal_device() -> str:
    """
    Automatically select the optimal device based on available hardware.

    Returns:
        str: Device name ("cuda", "mps", or "cpu")
    """
    if torch.cuda.is_available():
        device = "cuda"
        logger.info(f"Using CUDA device: {torch.cuda.get_device_name(0)}")
    elif torch.backends.mps.is_available():
        device = "mps"
        logger.info("Using MPS (Apple Silicon GPU) device")
    else:
        device = "cpu"
        logger.info("Using CPU device (inference will be slower)")

    return device


def get_torch_dtype(device: str) -> torch.dtype:
    """
    Get the appropriate torch dtype for the given device.

    Args:
        device: Device name ("cuda", "mps", or "cpu")

    Returns:
        torch.dtype: Recommended dtype for the device
    """
    if device == "cuda":
        # Use float16 for CUDA to save VRAM
        return torch.float16
    elif device == "mps":
        # MPS has better support for float32
        return torch.float32
    else:
        # CPU uses float32
        return torch.float32
