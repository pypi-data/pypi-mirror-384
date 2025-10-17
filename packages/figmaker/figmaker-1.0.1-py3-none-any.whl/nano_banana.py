#!/usr/bin/env python3
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
import argparse
import sys

# Check for API key
api_key = os.environ.get('GOOGLE_API_KEY')
if not api_key:
    print("Error: GOOGLE_API_KEY environment variable not set.", file=sys.stderr)
    print("\nPlease set your Google Gemini API key:", file=sys.stderr)
    print("  export GOOGLE_API_KEY='your-api-key-here'", file=sys.stderr)
    print("\nGet your API key at: https://aistudio.google.com/apikey", file=sys.stderr)
    sys.exit(1)

client = genai.Client(api_key=api_key)

def generate_image(prompt, output_path="generated_image.png", aspect_ratio=None):
    """
    Generate an image from a text prompt using Gemini Nano Banana.

    Args:
        prompt (str): Text description of the image to generate
        output_path (str): Path to save the generated image
        aspect_ratio (str): Optional aspect ratio (e.g., "16:9", "1:1", "9:16")

    Returns:
        str: Path to the saved image
    """
    config_params = {}
    if aspect_ratio:
        config_params['image_config'] = types.ImageConfig(aspect_ratio=aspect_ratio)

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt],
        config=types.GenerateContentConfig(**config_params) if config_params else None
    )

    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(f"Response text: {part.text}")
        elif part.inline_data is not None:
            image = Image.open(BytesIO(part.inline_data.data))
            image.save(output_path)
            print(f"Image saved to: {output_path}")
            return output_path

def edit_image(prompt, input_image_path, output_path="edited_image.png"):
    """
    Edit an existing image based on a text prompt.

    Args:
        prompt (str): Text description of the edits to make
        input_image_path (str): Path to the input image
        output_path (str): Path to save the edited image

    Returns:
        str: Path to the saved image
    """
    image = Image.open(input_image_path)

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt, image],
    )

    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(f"Response text: {part.text}")
        elif part.inline_data is not None:
            edited_image = Image.open(BytesIO(part.inline_data.data))
            edited_image.save(output_path)
            print(f"Edited image saved to: {output_path}")
            return output_path

def generate_image_only(prompt, output_path="generated_image.png"):
    """
    Generate an image without any text response.

    Args:
        prompt (str): Text description of the image to generate
        output_path (str): Path to save the generated image

    Returns:
        str: Path to the saved image
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_modalities=['Image']
        )
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            image = Image.open(BytesIO(part.inline_data.data))
            image.save(output_path)
            print(f"Image saved to: {output_path}")
            return output_path

def main():
    parser = argparse.ArgumentParser(
        description='Nano Banana - AI Image Generation and Editing CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate an image from text
  nanobanana generate "a cute cat" -o cat.png

  # Generate with aspect ratio
  nanobanana generate "sunset landscape" -o sunset.png --aspect-ratio 16:9

  # Edit an existing image
  nanobanana edit cat.jpg "add a wizard hat" -o wizard_cat.png

  # Generate image only (no text response)
  nanobanana generate-only "red panda sticker" -o panda.png
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate image from text prompt')
    generate_parser.add_argument('prompt', type=str, help='Text prompt for image generation')
    generate_parser.add_argument('-o', '--output', type=str, default='generated_image.png', help='Output file path')
    generate_parser.add_argument('--aspect-ratio', type=str, help='Aspect ratio (e.g., 16:9, 1:1, 9:16)')

    # Generate-only command
    generate_only_parser = subparsers.add_parser('generate-only', help='Generate image without text response')
    generate_only_parser.add_argument('prompt', type=str, help='Text prompt for image generation')
    generate_only_parser.add_argument('-o', '--output', type=str, default='generated_image.png', help='Output file path')

    # Edit command
    edit_parser = subparsers.add_parser('edit', help='Edit an existing image')
    edit_parser.add_argument('image', type=str, help='Path to input image')
    edit_parser.add_argument('prompt', type=str, help='Text prompt describing the edits')
    edit_parser.add_argument('-o', '--output', type=str, default='edited_image.png', help='Output file path')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'generate':
            print(f"Generating image: {args.prompt}")
            generate_image(args.prompt, args.output, args.aspect_ratio)
        elif args.command == 'generate-only':
            print(f"Generating image (no text): {args.prompt}")
            generate_image_only(args.prompt, args.output)
        elif args.command == 'edit':
            print(f"Editing image: {args.image}")
            print(f"Prompt: {args.prompt}")
            edit_image(args.prompt, args.image, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
