import asyncio
import logging
import random
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from config.settings import settings

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None
    ImageDraw = None

logger = logging.getLogger(__name__)

class ImageGenerator:
    """Generates illustrations for bedtime stories using Gemini Imagen, Pollinations.ai, or Pillow fallbacks."""

    def __init__(self) -> None:
        """Initializes the image generator with a thread pool executor."""
        self.executor = ThreadPoolExecutor(max_workers=4)

    def _generate_single_image(self, prompt: str, index: int) -> Path:
        """
        Worker task generating a single illustration via Imagen 3, Pollinations.ai, or drawing a styled placeholder.

        Args:
            prompt: The text prompt describing the image to generate.
            index: The index of the image (0 for cover, 1+ for scenes).

        Returns:
            The Path to the generated image file.
        """
        output_path: Path = settings.assets_dir / f"illustration_{index}.png"

        # Call Gemini Image Model if client and API key are configured
        if genai is not None and types is not None and settings.gemini_api_key:
            try:
                logger.info(f"Generating illustration using {settings.imagen_model_name} for: '{prompt[:50]}...'")
                client = genai.Client(api_key=settings.gemini_api_key)
                
                # Check if model name uses the new generate_content standard (typically has 'image' in the name)
                if "image" in settings.imagen_model_name:
                    response = client.models.generate_content(
                        model=settings.imagen_model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE"]
                        )
                    )
                    image_bytes: Any = None
                    for candidate in response.candidates:
                        for part in candidate.content.parts:
                            if part.inline_data:
                                image_bytes = part.inline_data.data
                                break
                    if image_bytes:
                        output_path.write_bytes(image_bytes)
                        logger.info(f"Gemini Image saved illustration to {output_path}")
                        return output_path
                    else:
                        raise ValueError("No image data returned in response parts.")
                else:
                    # Legacy Imagen generate_images API
                    result = client.models.generate_images(
                        model=settings.imagen_model_name,
                        prompt=prompt,
                        config=types.GenerateImagesConfig(
                            number_of_images=1,
                            output_mime_type="image/png",
                            aspect_ratio="1:1"
                        )
                    )
                    for generated_image in result.generated_images:
                        output_path.write_bytes(generated_image.image.image_bytes)
                    logger.info(f"Imagen saved illustration to {output_path}")
                    return output_path
            except Exception as e:
                logger.error(f"Image generation API failed: {e}. Trying free fallback image generator.")

        # Attempt to use Pollinations.ai (Free, High-Quality, No credits/billing needed)
        user_agents: list[str] = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edge/119.0.0.0'
        ]

        max_retries: int = 3
        for retry in range(max_retries):
            try:
                ssl_context = ssl._create_unverified_context()
                encoded_prompt: str = urllib.parse.quote(prompt)
                url: str = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=600&height=600&model=flux&nologo=true"
                logger.info(f"Generating free illustration via Pollinations.ai (Attempt {retry+1}/{max_retries}) for: '{prompt[:50]}...'")
                
                # Pick a random user-agent to bypass IP-based bot detection patterns
                ua: str = random.choice(user_agents)
                req = urllib.request.Request(
                    url, 
                    headers={'User-Agent': ua}
                )
                with urllib.request.urlopen(req, timeout=25, context=ssl_context) as response:
                    image_bytes = response.read()
                    if image_bytes and len(image_bytes) > 1000:
                        output_path.write_bytes(image_bytes)
                        logger.info(f"Successfully saved Pollinations.ai illustration to {output_path}")
                        return output_path
            except urllib.error.HTTPError as he:
                if he.code == 429:
                    wait_time: float = 2.0 + retry * 2.5 + random.random() * 1.5
                    logger.warning(f"Pollinations.ai returned 429 (Too Many Requests). Retrying in {wait_time:.2f}s...")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"Pollinations.ai HTTP Error {he.code}. Retrying...")
                    time.sleep(1.0)
            except Exception as pe:
                logger.warning(f"Pollinations.ai generation failed: {pe}. Retrying...")
                time.sleep(1.0)
        
        logger.warning("All Pollinations.ai generation retries exhausted. Falling back to styled PIL placeholder.")

        # Fallback drawing using PIL/Pillow
        if Image is not None and ImageDraw is not None:
            try:
                logger.info(f"Pillow drawing styled storybook slide placeholder for: '{prompt[:50]}'")
                colors: list[tuple[int, int, int]] = [
                    (45, 52, 54),   # Cover background
                    (108, 92, 231), # Slide 1 (violet)
                    (9, 132, 227),  # Slide 2 (blue)
                    (0, 184, 148)   # Slide 3 (green)
                ]
                bg_color: tuple[int, int, int] = colors[index % len(colors)]
                img = Image.new("RGB", (600, 600), color=bg_color)
                
                # Draw simple shapes representing child's book features
                draw = ImageDraw.Draw(img)
                draw.ellipse([150, 150, 450, 450], fill=(255, 234, 167), outline=(250, 177, 160), width=6)
                
                # Draw text summary on slide
                draw.text((20, 20), f"Slide {index}", fill=(255, 255, 255))
                draw.text((20, 550), f"Prompt: {prompt[:75]}...", fill=(255, 255, 255))
                
                # Pillow accepts Path objects directly for saving
                img.save(output_path, "PNG")
                return output_path
            except Exception as e:
                logger.error(f"Failed to draw Pillow styled fallback: {e}")
                
        # Bare minimal empty file creation if Pillow fails
        try:
            output_path.write_text("")
        except Exception:
            pass
        return output_path

    async def generate_illustrations_parallel(self, prompts: list[str]) -> list[Path]:
        """
        Triggers sequential image generation requests to prevent hitting Pollinations.ai IP concurrency rate limits.

        Args:
            prompts: A list of text prompts for image generation.

        Returns:
            A list of Paths of the generated illustrations.
        """
        logger.info(f"Generating {len(prompts)} illustrations sequentially.")
        loop = asyncio.get_running_loop()
        results: list[Path] = []
        for i, prompt in enumerate(prompts):
            res: Path = await loop.run_in_executor(self.executor, self._generate_single_image, prompt, i)
            results.append(res)
            # Sleep gently between requests to respect rate limits
            if i < len(prompts) - 1:
                await asyncio.sleep(4.0)
        return results

