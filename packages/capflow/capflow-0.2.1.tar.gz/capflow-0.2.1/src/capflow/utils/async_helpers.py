"""Async helper utilities for cross-platform compatibility."""

import asyncio
import sys
from typing import TypeVar, Coroutine

T = TypeVar("T")


def run_async(coro: Coroutine[None, None, T]) -> T:
    """
    Run an async coroutine with proper Windows Ctrl+C handling.

    This helper ensures that Ctrl+C (KeyboardInterrupt) works correctly
    on Windows when running async code. On Windows, asyncio sometimes
    doesn't handle SIGINT properly, making it difficult to interrupt
    running async tasks.

    Args:
        coro: Async coroutine to run

    Returns:
        Result of the coroutine

    Raises:
        KeyboardInterrupt: If user interrupts with Ctrl+C

    Example:
        >>> import capflow as cf
        >>> vlm = cf.VLM(api_key="...")
        >>>
        >>> async def process_image():
        >>>     return await vlm.generate_caption("image.jpg")
        >>>
        >>> # Works correctly on Windows with Ctrl+C
        >>> result = cf.run_async(process_image())
    """
    # On Windows, use WindowsSelectorEventLoopPolicy for better signal handling
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        return asyncio.run(coro)
    except KeyboardInterrupt:
        # Re-raise to allow graceful shutdown
        raise
