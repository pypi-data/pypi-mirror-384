"""
Tests for the Images primitive.
"""

import json
import time

import pytest
import responses

from langbase.constants import BASE_URL, IMAGES_ENDPOINT
from tests.constants import AUTH_AND_JSON_CONTENT_HEADER
from tests.validation_utils import validate_response_headers


@pytest.fixture
def mock_image_response():
    """Mock response for image generation."""
    timestamp = int(time.time())
    return {
        "id": "img-123456789",
        "provider": "openai",
        "model": "openai:gpt-image-1",
        "object": "image.generation",
        "created": timestamp,
        "choices": [
            {
                "logprobs": None,
                "finish_reason": "stop",
                "native_finish_reason": "stop",
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "images": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "https://example.com/generated-image.png"
                            },
                            "index": 0,
                        }
                    ],
                },
            }
        ],
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 0,
            "total_tokens": 15,
            "prompt_tokens_details": {"cached_tokens": 0},
            "completion_tokens_details": {"reasoning_tokens": 0, "image_tokens": 1},
        },
    }


class TestImages:
    """Test the Images primitive."""

    @responses.activate
    def test_images_generate_basic(self, langbase_client, mock_image_response):
        """Test images.generate method with basic parameters."""
        responses.add(
            responses.POST,
            f"{BASE_URL}{IMAGES_ENDPOINT}",
            json=mock_image_response,
            status=200,
        )

        result = langbase_client.images.generate(
            prompt="A futuristic cityscape with flying cars",
            model="openai:gpt-image-1",
            api_key="test-openai-key",
        )

        assert result == mock_image_response
        assert len(responses.calls) == 1
        request = responses.calls[0].request
        validate_response_headers(
            request.headers,
            {**AUTH_AND_JSON_CONTENT_HEADER, "LB-LLM-Key": "test-openai-key"},
        )
        request_body = json.loads(request.body)
        assert request_body["prompt"] == "A futuristic cityscape with flying cars"
        assert request_body["model"] == "openai:gpt-image-1"
        assert "api_key" not in request_body  # api_key should be in headers, not body

    @responses.activate
    def test_images_generate_with_dimensions(
        self, langbase_client, mock_image_response
    ):
        """Test images.generate method with width and height."""
        responses.add(
            responses.POST,
            f"{BASE_URL}{IMAGES_ENDPOINT}",
            json=mock_image_response,
            status=200,
        )

        result = langbase_client.images.generate(
            prompt="A serene mountain landscape",
            model="google:gemini-2.5-flash-image-preview",
            api_key="test-google-key",
            width=1024,
            height=768,
        )

        assert result == mock_image_response
        assert len(responses.calls) == 1
        request = responses.calls[0].request
        validate_response_headers(
            request.headers,
            {**AUTH_AND_JSON_CONTENT_HEADER, "LB-LLM-Key": "test-google-key"},
        )
        request_body = json.loads(request.body)
        assert request_body["width"] == 1024
        assert request_body["height"] == 768

    @responses.activate
    def test_images_generate_with_all_parameters(
        self, langbase_client, mock_image_response
    ):
        """Test images.generate method with all parameters."""
        responses.add(
            responses.POST,
            f"{BASE_URL}{IMAGES_ENDPOINT}",
            json=mock_image_response,
            status=200,
        )

        result = langbase_client.images.generate(
            prompt="A cyberpunk cityscape at night",
            model="together:black-forest-labs/FLUX.1-schnell-Free",
            api_key="test-together-key",
            width=1024,
            height=1024,
            steps=4,
            n=2,
        )

        assert result == mock_image_response
        assert len(responses.calls) == 1
        request = responses.calls[0].request
        validate_response_headers(
            request.headers,
            {**AUTH_AND_JSON_CONTENT_HEADER, "LB-LLM-Key": "test-together-key"},
        )
        request_body = json.loads(request.body)
        assert request_body["prompt"] == "A cyberpunk cityscape at night"
        assert request_body["model"] == "together:black-forest-labs/FLUX.1-schnell-Free"
        assert request_body["width"] == 1024
        assert request_body["height"] == 1024
        assert request_body["steps"] == 4
        assert request_body["n"] == 2

    @responses.activate
    def test_images_generate_with_image_url(self, langbase_client, mock_image_response):
        """Test images.generate method with image_url for image-to-image."""
        responses.add(
            responses.POST,
            f"{BASE_URL}{IMAGES_ENDPOINT}",
            json=mock_image_response,
            status=200,
        )

        result = langbase_client.images.generate(
            prompt="Make it more colorful",
            model="openai:gpt-image-1",
            api_key="test-openai-key",
            image_url="https://example.com/input-image.png",
        )

        assert result == mock_image_response
        assert len(responses.calls) == 1
        request = responses.calls[0].request
        request_body = json.loads(request.body)
        assert request_body["image_url"] == "https://example.com/input-image.png"

    @responses.activate
    def test_images_generate_with_kwargs(self, langbase_client, mock_image_response):
        """Test images.generate method with additional kwargs."""
        responses.add(
            responses.POST,
            f"{BASE_URL}{IMAGES_ENDPOINT}",
            json=mock_image_response,
            status=200,
        )

        result = langbase_client.images.generate(
            prompt="A fantasy landscape",
            model="openai:gpt-image-1",
            api_key="test-openai-key",
            quality="hd",
            style="vivid",
        )

        assert result == mock_image_response
        assert len(responses.calls) == 1
        request = responses.calls[0].request
        request_body = json.loads(request.body)
        assert request_body["quality"] == "hd"
        assert request_body["style"] == "vivid"

    def test_images_generate_missing_prompt(self, langbase_client):
        """Test that images.generate raises error when prompt is missing."""
        with pytest.raises(ValueError, match="Image generation prompt is required"):
            langbase_client.images.generate(
                prompt="",
                model="openai:gpt-image-1",
                api_key="test-key",
            )

    def test_images_generate_missing_model(self, langbase_client):
        """Test that images.generate raises error when model is missing."""
        with pytest.raises(ValueError, match="Image generation model is required"):
            langbase_client.images.generate(
                prompt="A test image",
                model="",
                api_key="test-key",
            )

    def test_images_generate_missing_api_key(self, langbase_client):
        """Test that images.generate raises error when api_key is missing."""
        with pytest.raises(ValueError, match="Image generation API key is required"):
            langbase_client.images.generate(
                prompt="A test image",
                model="openai:gpt-image-1",
                api_key="",
            )

    @responses.activate
    def test_images_generate_api_error(self, langbase_client):
        """Test images.generate method handles API errors."""
        responses.add(
            responses.POST,
            f"{BASE_URL}{IMAGES_ENDPOINT}",
            json={"error": "Invalid API key"},
            status=401,
        )

        with pytest.raises(Exception):
            langbase_client.images.generate(
                prompt="A test image",
                model="openai:gpt-image-1",
                api_key="invalid-key",
            )

    @responses.activate
    def test_images_generate_openrouter(self, langbase_client, mock_image_response):
        """Test images.generate with OpenRouter model."""
        responses.add(
            responses.POST,
            f"{BASE_URL}{IMAGES_ENDPOINT}",
            json=mock_image_response,
            status=200,
        )

        result = langbase_client.images.generate(
            prompt="A majestic dragon",
            model="openrouter:google/gemini-2.5-flash-image-preview",
            api_key="test-openrouter-key",
        )

        assert result == mock_image_response
        assert len(responses.calls) == 1
        request = responses.calls[0].request
        validate_response_headers(
            request.headers,
            {**AUTH_AND_JSON_CONTENT_HEADER, "LB-LLM-Key": "test-openrouter-key"},
        )
        request_body = json.loads(request.body)
        assert (
            request_body["model"] == "openrouter:google/gemini-2.5-flash-image-preview"
        )

    @responses.activate
    def test_images_generate_response_structure(
        self, langbase_client, mock_image_response
    ):
        """Test that the response has the correct structure."""
        responses.add(
            responses.POST,
            f"{BASE_URL}{IMAGES_ENDPOINT}",
            json=mock_image_response,
            status=200,
        )

        result = langbase_client.images.generate(
            prompt="Test image",
            model="openai:gpt-image-1",
            api_key="test-key",
        )

        # Verify response structure
        assert "id" in result
        assert "provider" in result
        assert "model" in result
        assert "object" in result
        assert "created" in result
        assert "choices" in result
        assert "usage" in result

        # Verify choices structure
        assert len(result["choices"]) > 0
        choice = result["choices"][0]
        assert "message" in choice
        assert "images" in choice["message"]
        assert len(choice["message"]["images"]) > 0
        assert "image_url" in choice["message"]["images"][0]
        assert "url" in choice["message"]["images"][0]["image_url"]

        # Verify usage structure
        assert "prompt_tokens" in result["usage"]
        assert "completion_tokens" in result["usage"]
        assert "total_tokens" in result["usage"]
