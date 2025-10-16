"""Vision Language Model tagger using Pydantic-AI."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Union, Optional

from PIL import Image
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.messages import ImageUrl

from .base import BaseModel

logger = logging.getLogger(__name__)


class VLM(BaseModel):
    """
    Vision Language Model tagger for verification and reconciliation.

    Uses VLM (GPT-5-mini by default) to verify and reconcile outputs from
    Florence2 and WD14, converting tags to natural language descriptions.
    """

    def __init__(
        self,
        model_name: str = "gpt-5-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ):
        """
        Initialize Vision Language Model.

        Supports both OpenAI and OpenRouter models:
        - OpenAI models: gpt-5, gpt-5-mini (default), gpt-5-nano, gpt-4o
        - OpenRouter models: google/gemini-2.5-flash, anthropic/claude-3.5-sonnet, etc.

        Args:
            model_name: Model name (default: gpt-5-mini for OpenAI)
            api_key: API key (required, or set OPENAI_API_KEY/OPENROUTER_API_KEY env var)
            base_url: API base URL (default: None for OpenAI, set to "https://openrouter.ai/api/v1" for OpenRouter)
            system_prompt: System prompt for the model

        Examples:
            # OpenAI (pass API key explicitly)
            vlm = VLM(api_key="your-openai-key")
            vlm = VLM(model_name="gpt-5", api_key="your-openai-key")

            # OpenAI (from environment variable)
            import os
            vlm = VLM(api_key=os.getenv("OPENAI_API_KEY"))

            # OpenRouter
            vlm = VLM(
                model_name="google/gemini-2.5-flash",
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY")
            )
        """
        self.model_name = model_name
        self.base_url = base_url

        # Determine API key based on base_url
        if base_url and "openrouter" in base_url:
            # OpenRouter mode
            self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "OpenRouter API key not found. "
                    "Set OPENROUTER_API_KEY environment variable or pass api_key parameter."
                )
        else:
            # OpenAI mode (default)
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "OpenAI API key not found. "
                    "Set OPENAI_API_KEY environment variable or pass api_key parameter."
                )

        # Default system prompt
        self.system_prompt = system_prompt or (
            "You are an expert at creating precise image generation prompts. "
            "Your goal is to describe images concisely for AI image generators. "
            "Write in a comma-separated, tag-like style optimized for Stable Diffusion, Midjourney, FLUX, etc. "
            "Be specific and accurate based on what you see. "
            "Do not invent details. Keep descriptions concise but informative. "
            "Focus on: medium type, subject, composition, technical details, and atmosphere."
        )

        # Initialize OpenAI-compatible model
        if self.base_url:
            # Custom base URL (e.g., OpenRouter)
            provider = OpenAIProvider(
                base_url=self.base_url,
                api_key=self.api_key,
            )
        else:
            # Default OpenAI
            provider = OpenAIProvider(
                api_key=self.api_key,
            )

        self.model = OpenAIChatModel(
            model_name=self.model_name,
            provider=provider,
        )

        # Create agent
        self.agent = Agent(
            model=self.model,
            system_prompt=self.system_prompt,
        )

        logger.info(f"Initialized VLM (model={model_name}, base_url={base_url or 'OpenAI'})")

    def _prepare_image_input(
        self, image: Union[str, Path, Image.Image]
    ) -> Union[ImageUrl, str]:
        """
        Prepare image input for the model.

        Args:
            image: Image path, URL, or PIL Image

        Returns:
            ImageUrl or base64 encoded image string
        """
        if isinstance(image, str):
            # Check if it's a URL
            if image.startswith(("http://", "https://")):
                return ImageUrl(url=image)
            else:
                # Local file path
                image_path = Path(image)
                if not image_path.exists():
                    raise FileNotFoundError(f"Image file not found: {image}")

                # Read and convert to bytes
                import base64
                with open(image_path, "rb") as f:
                    image_bytes = f.read()

                # Determine MIME type
                suffix = image_path.suffix.lower()
                mime_map = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".gif": "image/gif",
                    ".webp": "image/webp",
                }
                mime_type = mime_map.get(suffix, "image/jpeg")

                # Create data URL
                b64_image = base64.b64encode(image_bytes).decode("utf-8")
                return f"data:{mime_type};base64,{b64_image}"

        elif isinstance(image, Path):
            return self._prepare_image_input(str(image))

        elif isinstance(image, Image.Image):
            # Convert PIL Image to bytes
            import io
            import base64

            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            image_bytes = buffer.getvalue()
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            return f"data:image/png;base64,{b64_image}"

        else:
            raise TypeError(
                f"Image must be str, Path, or PIL.Image.Image, got {type(image)}"
            )

    async def generate_caption(
        self,
        image: Union[str, Path, Image.Image],
        context: Optional[str] = None,
        user_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Generate a detailed natural language caption for the image (async).

        This is the primary async method. For synchronous usage, use generate_caption_sync().

        Args:
            image: Image path, URL, or PIL Image object
            context: Additional context (e.g., tags from other models)
            user_prompt: Custom user prompt (overrides default)
            **kwargs: Additional arguments

        Returns:
            str: Generated caption

        Example:
            >>> vlm = VLM(api_key="...")
            >>> caption = await vlm.generate_caption("image.jpg")
        """
        # Prepare image input
        image_input = self._prepare_image_input(image)

        # Build prompt
        if user_prompt:
            prompt = user_prompt
        else:
            prompt = "Describe this image in detail."

        # Add context if provided
        if context:
            prompt += f"\n\nAdditional context from other analysis:\n{context}"

        # Build message list
        if isinstance(image_input, ImageUrl):
            messages = [prompt, image_input]
        else:
            # For base64 images, wrap in ImageUrl
            messages = [prompt, ImageUrl(url=image_input)]

        # Run agent asynchronously
        try:
            result = await self.agent.run(messages)
            return result.output
        except Exception as e:
            logger.error(f"Error generating caption: {e}")
            raise

    def generate_caption_sync(
        self,
        image: Union[str, Path, Image.Image],
        context: Optional[str] = None,
        user_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Generate a detailed natural language caption for the image (sync).

        This is a synchronous wrapper that works even when called from an async context.
        For async usage, prefer generate_caption().

        Args:
            image: Image path, URL, or PIL Image object
            context: Additional context (e.g., tags from other models)
            user_prompt: Custom user prompt (overrides default)
            **kwargs: Additional arguments

        Returns:
            str: Generated caption

        Example:
            >>> vlm = VLM(api_key="...")
            >>> caption = vlm.generate_caption_sync("image.jpg")
        """
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # If we're already in an event loop, run in a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.generate_caption(image, context, user_prompt, **kwargs)
                )
                return future.result()
        except RuntimeError:
            # No event loop running, we can use asyncio.run
            return asyncio.run(
                self.generate_caption(image, context, user_prompt, **kwargs)
            )

    async def generate_caption_with_tags(
        self,
        image: Union[str, Path, Image.Image],
        tags: list[str],
        user_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Generate a caption using tags as context (async).

        Args:
            image: Image path, URL, or PIL Image object
            tags: List of tags from other models (e.g., WD14)
            user_prompt: Custom user prompt
            **kwargs: Additional arguments

        Returns:
            str: Generated caption
        """
        # Format tags as context
        context = f"Tags: {', '.join(tags)}"

        return await self.generate_caption(
            image=image,
            context=context,
            user_prompt=user_prompt,
            **kwargs,
        )

    def generate_caption_with_tags_sync(
        self,
        image: Union[str, Path, Image.Image],
        tags: list[str],
        user_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Generate a caption using tags as context (sync).

        Args:
            image: Image path, URL, or PIL Image object
            tags: List of tags from other models (e.g., WD14)
            user_prompt: Custom user prompt
            **kwargs: Additional arguments

        Returns:
            str: Generated caption
        """
        # Format tags as context
        context = f"Tags: {', '.join(tags)}"

        return self.generate_caption_sync(
            image=image,
            context=context,
            user_prompt=user_prompt,
            **kwargs,
        )

    async def generate_tags(
        self,
        image: Union[str, Path, Image.Image],
        **kwargs,
    ) -> list[str]:
        """
        Generate tags for the image (async, not the primary use case for VLM).

        Note: This method extracts keywords from the generated caption.
        For dedicated tagging, use WD14 model instead.

        Args:
            image: Image path, URL, or PIL Image object
            **kwargs: Additional arguments

        Returns:
            list[str]: Extracted keywords
        """
        logger.warning(
            "VLM.generate_tags() extracts keywords from caption. "
            "For dedicated tagging, use WD14 model instead."
        )

        caption = await self.generate_caption(
            image,
            user_prompt="List the main visual elements in this image as comma-separated keywords.",
            **kwargs,
        )

        # Simple keyword extraction
        keywords = [k.strip() for k in caption.split(",")]
        return keywords

    def generate_tags_sync(
        self,
        image: Union[str, Path, Image.Image],
        **kwargs,
    ) -> list[str]:
        """
        Generate tags for the image (sync, not the primary use case for VLM).

        Note: This method extracts keywords from the generated caption.
        For dedicated tagging, use WD14 model instead.

        Args:
            image: Image path, URL, or PIL Image object
            **kwargs: Additional arguments

        Returns:
            list[str]: Extracted keywords
        """
        logger.warning(
            "VLM.generate_tags_sync() extracts keywords from caption. "
            "For dedicated tagging, use WD14 model instead."
        )

        caption = self.generate_caption_sync(
            image,
            user_prompt="List the main visual elements in this image as comma-separated keywords.",
            **kwargs,
        )

        # Simple keyword extraction
        keywords = [k.strip() for k in caption.split(",")]
        return keywords

    async def refine_caption(
        self,
        image: Union[str, Path, Image.Image],
        draft_caption: str,
        refinement_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Refine an existing caption with visual verification (async).

        Args:
            image: Image path, URL, or PIL Image object
            draft_caption: Initial caption to refine
            refinement_prompt: Custom refinement instructions
            **kwargs: Additional arguments

        Returns:
            str: Refined caption
        """
        if refinement_prompt:
            prompt = refinement_prompt
        else:
            prompt = (
                "Here is a draft caption for this image:\n\n"
                f"{draft_caption}\n\n"
                "Please review the image and refine this caption to be more accurate, "
                "detailed, and natural. Correct any inaccuracies and add relevant details."
            )

        return await self.generate_caption(image, user_prompt=prompt, **kwargs)

    def refine_caption_sync(
        self,
        image: Union[str, Path, Image.Image],
        draft_caption: str,
        refinement_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Refine an existing caption with visual verification (sync).

        Args:
            image: Image path, URL, or PIL Image object
            draft_caption: Initial caption to refine
            refinement_prompt: Custom refinement instructions
            **kwargs: Additional arguments

        Returns:
            str: Refined caption
        """
        if refinement_prompt:
            prompt = refinement_prompt
        else:
            prompt = (
                "Here is a draft caption for this image:\n\n"
                f"{draft_caption}\n\n"
                "Please review the image and refine this caption to be more accurate, "
                "detailed, and natural. Correct any inaccuracies and add relevant details."
            )

        return self.generate_caption_sync(image, user_prompt=prompt, **kwargs)

    def __repr__(self) -> str:
        return f"VLM(model_name='{self.model_name}')"
