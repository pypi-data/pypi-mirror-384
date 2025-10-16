"""WD14 tagger models for anime/illustration image tagging."""

import csv
import logging
import warnings
from pathlib import Path
from typing import Literal, Optional, Union

import timm
import torch
from huggingface_hub import hf_hub_download
from PIL import Image
from timm.data.config import resolve_data_config
from timm.data.transforms_factory import create_transform

from ..utils.device import get_optimal_device
from .base import BaseModel

logger = logging.getLogger(__name__)

MODEL_NAMES = Literal["wd-eva02-large-tagger-v3", "wd-vit-large-tagger-v3"]

MODEL_REPO_MAP = {
    "wd-eva02-large-tagger-v3": "SmilingWolf/wd-eva02-large-tagger-v3",
    "wd-vit-large-tagger-v3": "SmilingWolf/wd-vit-large-tagger-v3",
}


class WD14(BaseModel):
    """
    WD14 (Waifu Diffusion 14) tagger for anime/illustration images.

    Supports danbooru-style tagging with ratings, characters, and general tags.
    """

    def __init__(
        self,
        model_name: MODEL_NAMES = "wd-eva02-large-tagger-v3",
        device: Optional[str] = None,
        general_threshold: float = 0.35,
        character_threshold: float = 0.75,
    ):
        """
        Initialize WD14 tagger.

        Args:
            model_name: Model name
            device: Target device ("cuda", "mps", "cpu"). Auto-detected if None.
            general_threshold: Threshold for general tags
            character_threshold: Threshold for character tags
        """
        self.model_name = model_name
        self.repo_id = MODEL_REPO_MAP[model_name]
        self.device = device or get_optimal_device()
        self.general_threshold = general_threshold
        self.character_threshold = character_threshold

        self.model = None
        self.transform = None
        self.tags_df = None
        self.rating_tags = None
        self.general_tags = None
        self.character_tags = None

        logger.info(f"Initialized WD14 (model={model_name}, device={self.device})")

    def _load_model(self):
        """Lazy load the model, transform, and tag labels."""
        if self.model is not None:
            return

        logger.info(f"Loading WD14 model: {self.model_name}")

        # Download model file
        model_path = hf_hub_download(
            repo_id=self.repo_id,
            filename="model.safetensors",
        )

        # Download CSV file
        csv_path = hf_hub_download(
            repo_id=self.repo_id,
            filename="selected_tags.csv",
        )

        # Load tags CSV with standard library
        self.rating_tags = []
        self.general_tags = []
        self.character_tags = []

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tag_name = row["name"]
                category = int(row["category"])

                if category == 9:  # Rating tags
                    self.rating_tags.append(tag_name)
                elif category == 0:  # General tags
                    self.general_tags.append(tag_name)
                elif category == 4:  # Character tags
                    self.character_tags.append(tag_name)

        # Load model with timm using HuggingFace Hub prefix
        self.model = timm.create_model(
            f"hf-hub:{self.repo_id}",
            pretrained=True,
            pretrained_cfg_overlay={"file": model_path},
        ).to(self.device)
        self.model.eval()

        # Create transform
        data_config = resolve_data_config(self.model.pretrained_cfg)
        self.transform = create_transform(**data_config)

        logger.info("Model loaded successfully")
        logger.info(
            f"Tags loaded: {len(self.rating_tags)} ratings, "
            f"{len(self.general_tags)} general, {len(self.character_tags)} characters"
        )

    def _load_image(self, image: Union[str, Path, Image.Image]) -> Image.Image:
        """
        Load image from path or return PIL Image as-is.

        Args:
            image: Image path or PIL Image

        Returns:
            PIL Image object
        """
        if isinstance(image, (str, Path)):
            return Image.open(image).convert("RGB")
        elif isinstance(image, Image.Image):
            return image.convert("RGB")
        else:
            raise TypeError(f"Image must be str, Path, or PIL.Image.Image, got {type(image)}")

    def predict(
        self,
        image: Union[str, Path, Image.Image],
    ) -> dict[str, any]:
        """
        Run prediction and return raw probabilities.

        Args:
            image: Image path or PIL Image object

        Returns:
            dict with ratings, general_probs, and character_probs
        """
        self._load_model()

        # Load and preprocess image
        pil_image = self._load_image(image)
        input_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)

        # Run inference
        with torch.no_grad():
            logits = self.model(input_tensor)
            probs = torch.sigmoid(logits[0]).cpu().numpy()

        # Split into tag categories
        rating_probs = probs[: len(self.rating_tags)]
        general_probs = probs[len(self.rating_tags) : len(self.rating_tags) + len(self.general_tags)]
        character_probs = probs[
            len(self.rating_tags) + len(self.general_tags) : len(self.rating_tags)
            + len(self.general_tags)
            + len(self.character_tags)
        ]

        # Create rating dict
        ratings = {tag: float(prob) for tag, prob in zip(self.rating_tags, rating_probs)}

        return {
            "ratings": ratings,
            "general_probs": general_probs,
            "character_probs": character_probs,
        }

    def generate_tags(
        self,
        image: Union[str, Path, Image.Image],
        general_threshold: Optional[float] = None,
        character_threshold: Optional[float] = None,
        **kwargs,
    ) -> list[str]:
        """
        Generate tags for the given image.

        Args:
            image: Image path or PIL Image object
            general_threshold: Threshold for general tags (uses default if None)
            character_threshold: Threshold for character tags (uses default if None)
            **kwargs: Additional arguments

        Returns:
            list[str]: List of tags above threshold
        """
        general_threshold = general_threshold or self.general_threshold
        character_threshold = character_threshold or self.character_threshold

        result = self.predict(image)

        tags = []

        # Add general tags
        for tag, prob in zip(self.general_tags, result["general_probs"]):
            if prob >= general_threshold:
                tags.append(tag)

        # Add character tags
        for tag, prob in zip(self.character_tags, result["character_probs"]):
            if prob >= character_threshold:
                tags.append(tag)

        return tags

    def generate_caption(
        self,
        image: Union[str, Path, Image.Image],
        **kwargs,
    ) -> str:
        """
        Generate a caption from tags (comma-separated).

        Args:
            image: Image path or PIL Image object
            **kwargs: Additional arguments passed to generate_tags

        Returns:
            str: Comma-separated tags
        """
        tags = self.generate_tags(image, **kwargs)
        return ", ".join(tags)

    def generate_tags_with_scores(
        self,
        image: Union[str, Path, Image.Image],
        general_threshold: Optional[float] = None,
        character_threshold: Optional[float] = None,
    ) -> dict[str, float]:
        """
        Generate tags with confidence scores.

        Args:
            image: Image path or PIL Image object
            general_threshold: Threshold for general tags
            character_threshold: Threshold for character tags

        Returns:
            dict[str, float]: Tag names mapped to confidence scores
        """
        general_threshold = general_threshold or self.general_threshold
        character_threshold = character_threshold or self.character_threshold

        result = self.predict(image)

        tags_with_scores = {}

        # Add general tags
        for tag, prob in zip(self.general_tags, result["general_probs"]):
            if prob >= general_threshold:
                tags_with_scores[tag] = float(prob)

        # Add character tags
        for tag, prob in zip(self.character_tags, result["character_probs"]):
            if prob >= character_threshold:
                tags_with_scores[tag] = float(prob)

        return tags_with_scores

    def get_rating(
        self,
        image: Union[str, Path, Image.Image],
    ) -> tuple[str, float]:
        """
        Get the most likely rating for the image.

        Args:
            image: Image path or PIL Image object

        Returns:
            tuple[str, float]: (rating_name, confidence)
        """
        result = self.predict(image)
        ratings = result["ratings"]

        # Find highest rating
        best_rating = max(ratings.items(), key=lambda x: x[1])

        return best_rating

    def __repr__(self) -> str:
        return f"WD14(model_name='{self.model_name}', device='{self.device}')"
