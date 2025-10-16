"""Florence2 model wrapper for image captioning and visual understanding."""

import logging
from pathlib import Path
from typing import Union, Literal, Optional
import warnings

import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM

from .base import BaseModel
from ..utils.device import get_optimal_device, get_torch_dtype

logger = logging.getLogger(__name__)

# Suppress flash_attn warnings on MPS
warnings.filterwarnings("ignore", message=".*flash_attn.*")


CaptionTask = Literal["caption", "detailed_caption", "more_detailed_caption"]
MODEL_SIZE = Literal["base", "large"]

TASK_PROMPTS = {
    "caption": "<CAPTION>",
    "detailed_caption": "<DETAILED_CAPTION>",
    "more_detailed_caption": "<MORE_DETAILED_CAPTION>",
}


class Florence2(BaseModel):
    """
    Florence2 vision-language tagger for image captioning.

    Supports multiple caption detail levels and cross-platform inference
    (CUDA, MPS, CPU).
    """

    def __init__(
        self,
        model_size: MODEL_SIZE = "base",
        device: Optional[str] = None,
        trust_remote_code: bool = True,
    ):
        """
        Initialize Florence2 model.

        Args:
            model_size: Model size ("base" or "large")
            device: Target device ("cuda", "mps", "cpu"). Auto-detected if None.
            trust_remote_code: Whether to trust remote code from HuggingFace
        """
        self.model_size = model_size
        self.model_name = f"microsoft/Florence-2-{model_size}"
        self.device = device or get_optimal_device()
        self.torch_dtype = get_torch_dtype(self.device)
        self.trust_remote_code = trust_remote_code

        self.model = None
        self.processor = None

        logger.info(
            f"Initialized Florence2 (size={model_size}, device={self.device}, dtype={self.torch_dtype})"
        )

    def _load_model(self):
        """Lazy load the model and processor."""
        if self.model is not None and self.processor is not None:
            return

        logger.info(f"Loading Florence2 model: {self.model_name}")

        # Load processor
        self.processor = AutoProcessor.from_pretrained(
            self.model_name,
            trust_remote_code=self.trust_remote_code,
        )

        # Load model
        # Use eager attention implementation to avoid SDPA compatibility issues
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=self.torch_dtype,
            trust_remote_code=self.trust_remote_code,
            attn_implementation="eager",
        ).to(self.device)

        logger.info("Model loaded successfully")

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
            raise TypeError(
                f"Image must be str, Path, or PIL.Image.Image, got {type(image)}"
            )

    def generate_caption(
        self,
        image: Union[str, Path, Image.Image],
        task: CaptionTask = "detailed_caption",
        max_new_tokens: int = 1024,
        num_beams: int = 3,
        do_sample: bool = False,
        temperature: float = 1.0,
        repetition_penalty: float = 1.0,
    ) -> str:
        """
        Generate a caption for the given image.

        Args:
            image: Image path or PIL Image object
            task: Caption detail level
            max_new_tokens: Maximum tokens to generate
            num_beams: Number of beams for beam search
            do_sample: Whether to use sampling
            temperature: Sampling temperature (lower = more conservative)
            repetition_penalty: Penalty for repeating tokens

        Returns:
            str: Generated caption
        """
        self._load_model()

        # Load and prepare image
        pil_image = self._load_image(image)

        # Get task prompt
        if task not in TASK_PROMPTS:
            raise ValueError(
                f"Invalid task: {task}. Must be one of {list(TASK_PROMPTS.keys())}"
            )
        prompt = TASK_PROMPTS[task]

        # Prepare inputs
        inputs = self.processor(
            text=prompt,
            images=pil_image,
            return_tensors="pt",
        ).to(self.device, self.torch_dtype)

        # Generate
        with torch.no_grad():
            generated_ids = self.model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=max_new_tokens,
                num_beams=num_beams,
                do_sample=do_sample,
                temperature=temperature if do_sample else 1.0,
                repetition_penalty=repetition_penalty,
                use_cache=False,  # Disable KV cache to avoid compatibility issues
            )

        # Decode
        generated_text = self.processor.batch_decode(
            generated_ids, skip_special_tokens=False
        )[0]

        # Parse the result
        parsed_answer = self.processor.post_process_generation(
            generated_text,
            task=prompt,
            image_size=(pil_image.width, pil_image.height),
        )

        # Extract caption text
        caption = parsed_answer.get(prompt, "")

        return caption

    def generate_tags(
        self,
        image: Union[str, Path, Image.Image],
        **kwargs,
    ) -> list[str]:
        """
        Generate tags for the given image.

        Note: Florence2 doesn't have a dedicated tagging mode.
        This uses detailed caption and extracts key phrases.

        Args:
            image: Image path or PIL Image object
            **kwargs: Additional arguments

        Returns:
            list[str]: List of tags (currently returns empty list)
        """
        # Florence2 doesn't have native tag generation
        # This will be handled by Wd14 model
        logger.warning(
            "Florence2 doesn't support tag generation. Use Wd14 model instead."
        )
        return []

    def __repr__(self) -> str:
        return f"Florence2(model_size='{self.model_size}', device='{self.device}')"
