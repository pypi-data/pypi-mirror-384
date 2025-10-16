"""Base model interface for captionflow."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union
from PIL import Image


class BaseModel(ABC):
    """Abstract base class for image captioning models."""

    @abstractmethod
    def generate_caption(
        self,
        image: Union[str, Path, Image.Image],
        **kwargs,
    ) -> str:
        """
        Generate a caption for the given image.

        Args:
            image: Image path or PIL Image object
            **kwargs: Model-specific keyword arguments

        Returns:
            str: Generated caption
        """
        pass

    @abstractmethod
    def generate_tags(
        self,
        image: Union[str, Path, Image.Image],
        **kwargs,
    ) -> list[str]:
        """
        Generate tags for the given image.

        Args:
            image: Image path or PIL Image object
            **kwargs: Model-specific keyword arguments

        Returns:
            list[str]: List of generated tags
        """
        pass
