"""
Images API client for the Langbase SDK.
"""

from typing import Any, Dict, Optional

from langbase.constants import IMAGES_ENDPOINT
from langbase.request import Request
from langbase.types import ImageGenerationResponse


class Images:
    """
    Client for image generation operations.

    This class provides methods for generating images using various AI providers.
    """

    def __init__(self, parent):
        """
        Initialize the Images client.

        Args:
            parent: The parent Langbase instance
        """
        self.parent = parent
        self.request: Request = parent.request

    def generate(
        self,
        prompt: str,
        model: str,
        api_key: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        image_url: Optional[str] = None,
        steps: Optional[int] = None,
        n: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ImageGenerationResponse:
        """
        Generate images using various AI providers.

        Args:
            prompt: The text prompt to generate images from
            model: The model to use for image generation
            api_key: The API key for the image generation provider
            width: Optional width of the generated image
            height: Optional height of the generated image
            image_url: Optional URL of an image for image-to-image generation
            steps: Optional number of generation steps
            n: Optional number of images to generate
            negative_prompt: Optional negative prompt to avoid certain elements
            **kwargs: Additional parameters for image generation

        Returns:
            ImageGenerationResponse containing generated images

        Raises:
            ValueError: If required options are missing
            Exception: If the API request fails
        """
        # Comprehensive input validation
        if not prompt:
            raise ValueError("Image generation prompt is required.")

        if not model:
            raise ValueError("Image generation model is required.")

        if not api_key:
            raise ValueError("Image generation API key is required.")

        # Build image parameters
        image_params: Dict[str, Any] = {
            "prompt": prompt,
            "model": model,
            "width": width,
            "height": height,
            "image_url": image_url,
            "steps": steps,
            "n": n,
            "negative_prompt": negative_prompt,
            **kwargs,
        }

        # Filter out None values
        image_params = {k: v for k, v in image_params.items() if v is not None}

        try:
            return self.request.post(
                IMAGES_ENDPOINT, image_params, headers={"LB-LLM-Key": api_key}
            )
        except Exception as error:
            raise Exception(f"Image generation failed: {str(error)}")
