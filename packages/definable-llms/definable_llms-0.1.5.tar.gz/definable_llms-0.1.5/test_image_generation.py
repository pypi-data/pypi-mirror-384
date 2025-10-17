#!/usr/bin/env python3
"""Test script for image generation functionality."""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from definable.llms.providers.openai.client import OpenAIProvider
from definable.llms.base.types import ImageRequest, ImageSize, ImageQuality, ImageStyle
from definable.llms.config import settings


async def test_image_generation():
  """Test DALL-E image generation functionality."""
  print("Testing Image Generation Functionality")
  print("=" * 50)

  # Initialize provider with API key from settings
  try:
    # Get the API key from settings
    api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else None
    if not api_key:
      print("✗ No OpenAI API key found")
      print("\nTo test image generation, you need to:")
      print("1. Set OPENAI_API_KEY environment variable")
      print("2. Or create a .env file with OPENAI_API_KEY=your_key")
      return False

    provider = OpenAIProvider(api_key=api_key)
    print("✓ OpenAI provider initialized")
  except Exception as e:
    print(f"✗ Failed to initialize OpenAI provider: {e}")
    return False

  # Test prompts
  test_prompts = [
    "A serene landscape with mountains and a lake at sunset",
    "A cute robot sitting at a desk reading a book",
    "Abstract geometric patterns in vibrant colors",
  ]

  print(f"\nTesting with {len(test_prompts)} different prompts...")

  for i, prompt in enumerate(test_prompts, 1):
    print(f"\n{i}. Testing prompt: '{prompt}'")

    # Create image request
    image_request = ImageRequest(
      prompt=prompt,
      model="dall-e-3",
      n=1,
      size=ImageSize.SMALL,  # Use smaller size for faster testing
      quality=ImageQuality.STANDARD,
      style=ImageStyle.VIVID,
      response_format="url",
    )

    try:
      print("   Sending request to DALL-E...")
      response = await provider.generate_image(image_request)

      print("   ✓ Image generated successfully!")
      print(f"   - Created: {response.created}")
      print(f"   - Images: {len(response.data)}")

      for j, image_data in enumerate(response.data):
        print(f"   - Image {j + 1}: {image_data.url}")
        if image_data.revised_prompt:
          print(f"     Revised prompt: {image_data.revised_prompt}")

    except Exception as e:
      print(f"   ✗ Failed to generate image: {e}")
      return False

  print("\n" + "=" * 50)
  print("✓ All image generation tests passed!")
  print("\nNext steps:")
  print("- Check the generated images using the URLs above")
  print("- Try different prompts, sizes, and styles")
  print("- Integrate image generation into your applications")

  return True


async def test_different_models():
  """Test different DALL-E models."""
  print("\nTesting Different Models")
  print("-" * 30)

  try:
    api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else None
    if not api_key:
      print("✗ No API key available for model testing")
      return

    provider = OpenAIProvider(api_key=api_key)

    models_to_test = ["dall-e-2", "dall-e-3"]
    prompt = "A simple drawing of a house with a garden"

    for model in models_to_test:
      print(f"\nTesting {model}...")

      # Different parameters for different models
      if model == "dall-e-2":
        image_request = ImageRequest(
          prompt=prompt,
          model=model,
          n=1,
          size=ImageSize.MEDIUM,  # DALL-E 2 supports different sizes
          response_format="url",
        )
      else:  # DALL-E 3
        image_request = ImageRequest(
          prompt=prompt,
          model=model,
          n=1,
          size=ImageSize.SMALL,
          quality=ImageQuality.STANDARD,
          style=ImageStyle.NATURAL,
          response_format="url",
        )

      try:
        response = await provider.generate_image(image_request)
        print(f"   ✓ {model} generated image successfully!")
        print(f"   - URL: {response.data[0].url}")

      except Exception as e:
        print(f"   ✗ {model} failed: {e}")

  except Exception as e:
    print(f"✗ Model testing failed: {e}")


async def main():
  """Main test function."""
  success = await test_image_generation()

  if success:
    await test_different_models()

  print("\nImage generation testing completed!")


if __name__ == "__main__":
  asyncio.run(main())
