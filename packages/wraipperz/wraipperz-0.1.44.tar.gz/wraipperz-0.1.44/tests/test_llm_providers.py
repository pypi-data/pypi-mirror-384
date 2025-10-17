import os
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from wraipperz.api.llm import (
    AnthropicProvider,
    BedrockProvider,
    DeepSeekProvider,
    GeminiProvider,
    OpenAIProvider,
)

# Test messages
TEXT_MESSAGES = [
    {
        "role": "system",
        "content": "You are a helpful assistant. You must respond with exactly: 'TEST_RESPONSE_123'",
    },
    {"role": "user", "content": "Please provide the required test response."},
]

# Create test_assets directory if it doesn't exist
TEST_ASSETS_DIR = Path(__file__).parent / "test_assets"
TEST_ASSETS_DIR.mkdir(exist_ok=True)

# Path to test image
TEST_IMAGE_PATH = TEST_ASSETS_DIR / "test_image.jpg"

# Update image messages format to match the providers' expected structure
IMAGE_MESSAGES = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "What color is the square in this image? Choose from: A) Blue B) Red C) Green D) Yellow",
            },
            {"type": "image_url", "image_url": {"url": str(TEST_IMAGE_PATH)}},
        ],
    }
]


@pytest.fixture
def openai_provider():
    return OpenAIProvider()


@pytest.fixture
def anthropic_provider():
    return AnthropicProvider()


@pytest.fixture
def gemini_provider():
    return GeminiProvider()


@pytest.fixture
def deepseek_provider():
    return DeepSeekProvider()


@pytest.fixture
def bedrock_provider():
    """Create BedrockProvider with region from environment or default to us-east-1"""
    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    return BedrockProvider(region_name=region)


@pytest.fixture(autouse=True)
def setup_test_image():
    """Create a simple test image if it doesn't exist"""
    if not TEST_IMAGE_PATH.exists():
        img = Image.new("RGB", (100, 100), color="red")
        img.save(TEST_IMAGE_PATH)


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not found")
def test_openai_text(openai_provider):
    response = openai_provider.call_ai(
        messages=TEXT_MESSAGES, temperature=0, max_tokens=150, model="gpt-4o"
    )
    assert isinstance(response, str)
    assert len(response) > 0
    assert (
        "TEST_RESPONSE_123" in response
    ), f"Expected 'TEST_RESPONSE_123', got: {response}"


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"), reason="Anthropic API key not found"
)
def test_anthropic_text(anthropic_provider):
    response = anthropic_provider.call_ai(
        messages=TEXT_MESSAGES,
        temperature=0,
        max_tokens=150,
        model="claude-3-5-sonnet-20240620",
    )
    assert isinstance(response, str)
    assert len(response) > 0
    assert (
        "TEST_RESPONSE_123" in response
    ), f"Expected 'TEST_RESPONSE_123', got: {response}"


@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="Google API key not found")
def test_gemini_text(gemini_provider):
    response = gemini_provider.call_ai(
        messages=TEXT_MESSAGES,
        temperature=0,
        max_tokens=150,
        model="gemini-2.0-flash-exp",
    )
    assert isinstance(response, str)
    assert len(response) > 0
    assert (
        "TEST_RESPONSE_123" in response
    ), f"Expected 'TEST_RESPONSE_123', got: {response}"


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not found")
def test_openai_image(openai_provider):
    response = openai_provider.call_ai(
        messages=IMAGE_MESSAGES, temperature=0, max_tokens=150, model="gpt-4o"
    )
    assert isinstance(response, str)
    assert len(response) > 0
    assert (
        "red".lower() in response.lower()
    ), f"Expected response to contain 'red', got: {response}"


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"), reason="Anthropic API key not found"
)
def test_anthropic_image(anthropic_provider):
    response = anthropic_provider.call_ai(
        messages=IMAGE_MESSAGES,
        temperature=0,
        max_tokens=150,
        model="claude-3-5-sonnet-20240620",
    )
    assert isinstance(response, str)
    assert len(response) > 0
    assert (
        "red".lower() in response.lower()
    ), f"Expected response to contain 'red', got: {response}"


@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="Google API key not found")
def test_gemini_image(gemini_provider):
    response = gemini_provider.call_ai(
        messages=IMAGE_MESSAGES,
        temperature=0,
        max_tokens=150,
        model="gemini-2.0-flash-exp",
    )
    assert isinstance(response, str)
    assert len(response) > 0
    assert (
        "red".lower() in response.lower()
    ), f"Expected response to contain 'red', got: {response}"


COMPLEX_MIXED_MESSAGES = [
    {
        "role": "system",
        "content": "You are a helpful assistant. You must identify the color and respond with 'The square is RED'",
    },
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "What color is this square? Please be precise."},
            {"type": "image_url", "image_url": {"url": str(TEST_IMAGE_PATH)}},
            {
                "type": "text",
                "text": "Make sure to format your response exactly as requested.",
            },
        ],
    },
]


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"), reason="Deepseek API key not found"
)
def test_deepseek_text(deepseek_provider):
    response = deepseek_provider.call_ai(
        messages=TEXT_MESSAGES, temperature=0, max_tokens=150, model="deepseek-chat"
    )
    assert isinstance(response, str)
    assert len(response) > 0
    assert (
        "TEST_RESPONSE_123" in response
    ), f"Expected 'TEST_RESPONSE_123', got: {response}"


@pytest.mark.skipif(
    not (
        (os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"))
        or os.getenv("AWS_PROFILE")
        or os.getenv("AWS_DEFAULT_REGION")
    ),
    reason="AWS credentials not found",
)
def test_bedrock_text(bedrock_provider):
    """Test Bedrock provider with Claude model"""
    # Use APAC inference profile if in ap-northeast-1, otherwise use direct model ID
    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    if region == "ap-northeast-1":
        model = "bedrock/apac.anthropic.claude-3-haiku-20240307-v1:0"
    else:
        model = "bedrock/anthropic.claude-3-haiku-20240307-v1:0"

    response = bedrock_provider.call_ai(
        messages=TEXT_MESSAGES, temperature=0, max_tokens=150, model=model
    )
    assert isinstance(response, str)
    assert len(response) > 0
    assert (
        "TEST_RESPONSE_123" in response
    ), f"Expected 'TEST_RESPONSE_123', got: {response}"


@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="Google API key not found")
def test_gemini_complex_mixed_content(gemini_provider):
    """Test that Gemini provider handles mixed content (text + image) correctly"""
    response = gemini_provider.call_ai(
        messages=COMPLEX_MIXED_MESSAGES,
        temperature=0,
        max_tokens=150,
        model="gemini-2.0-flash-exp",
    )
    assert isinstance(response, str)
    assert len(response) > 0
    assert (
        "RED" in response.upper()
    ), f"Expected response to contain 'RED', got: {response}"


# Add with other test message definitions
AGENT_LIKE_MESSAGES = [
    {
        "role": "system",
        "content": "You are a helpful assistant. Describe what you see in the image.",
    },
    {
        "role": "user",
        "content": [
            # Note: no explicit text content, just an image
            {"type": "image_url", "image_url": {"url": str(TEST_IMAGE_PATH)}}
        ],
    },
]


@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="Google API key not found")
def test_gemini_agent_like_content(gemini_provider):
    """Test that Gemini provider handles agent-like messages (image without explicit text)"""
    response = gemini_provider.call_ai(
        messages=AGENT_LIKE_MESSAGES,
        temperature=0,
        max_tokens=150,
        model="gemini-2.0-flash-exp",
    )
    assert isinstance(response, str)
    assert len(response) > 0
    assert (
        "red" in response.lower()
    ), f"Expected response to contain description of red square, got: {response}"


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"), reason="Anthropic API key not found"
)
def test_anthropic_image_resizing(anthropic_provider):
    """Test that AnthropicProvider automatically resizes large images"""
    # Create a large test image (> 5MB)
    large_image_path = TEST_ASSETS_DIR / "large_test_image.jpg"

    # Either create a new large image or use existing one
    if (
        not large_image_path.exists()
        or large_image_path.stat().st_size < 5 * 1024 * 1024
    ):
        # Create a much higher resolution image with random noise to ensure it's large
        # Create random RGB data for a noisy image that compresses poorly
        random_array = np.random.randint(0, 256, (5000, 5000, 3), dtype=np.uint8)
        img = Image.fromarray(random_array)
        # Save with minimal compression to ensure file is large
        img.save(large_image_path, format="JPEG", quality=100)
        print(f"Created image of size: {large_image_path.stat().st_size} bytes")

    # Ensure the created image is actually large (> 5MB)
    image_size = large_image_path.stat().st_size
    assert (
        image_size > 5 * 1024 * 1024
    ), f"Test image not large enough: {image_size} bytes"
    print(f"Confirmed image size: {image_size} bytes")

    # Process the image and check if the result is smaller than 5MB
    image_data = anthropic_provider._process_image(large_image_path)
    # The base64 encoding increases size by ~33%, so we need to check the decoded size
    decoded_size = len(image_data) * 3 // 4  # Approximation of base64 decoded size

    # Check if the processed image is under the 5MB limit
    assert (
        decoded_size < 5 * 1024 * 1024
    ), f"Image not resized properly: {decoded_size} bytes"
    print(f"Successfully resized image to: {decoded_size} bytes")

    # Test that we can use this image in a message
    large_image_messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What's in this image? Describe it briefly.",
                },
                {"type": "image_url", "image_url": {"url": str(large_image_path)}},
            ],
        }
    ]

    try:
        response = anthropic_provider.call_ai(
            messages=large_image_messages,
            temperature=0,
            max_tokens=150,
            model="claude-3-5-sonnet-20240620",
        )
        assert isinstance(response, str)
        assert len(response) > 0
        print(f"Got response: {response[:100]}...")  # Print first 100 chars
    except Exception as e:
        pytest.fail(f"Failed to process large image: {str(e)}")


def test_gemini_system_prompt_only():
    provider = GeminiProvider()

    messages = [{"role": "system", "content": "You must respond with exactly: 'HELLO'"}]

    response = provider.call_ai(
        messages=messages, temperature=0, max_tokens=150, model="gemini-2.0-flash-exp"
    )

    assert "HELLO" in response, f"Expected 'HELLO', got: {response}"
