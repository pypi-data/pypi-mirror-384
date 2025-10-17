# FigMaker

AI-powered image generation and editing CLI tool using Gemini Nano Banana API.

## Installation

```bash
pip install figmaker
```

## Quick Start

```bash
# Generate an image from text
figmaker generate "a cute cat wearing sunglasses" -o cat.png

# Generate with custom aspect ratio
figmaker generate "sunset over mountains" --aspect-ratio 16:9 -o sunset.png

# Edit an existing image
figmaker edit photo.jpg "add a wizard hat on the person" -o edited.png

# Generate image without text response
figmaker generate-only "kawaii red panda sticker" -o sticker.png
```

## Setup

Before using FigMaker, you need a Google Gemini API key:

1. Get your API key from [Google AI Studio](https://aistudio.google.com/apikey)
2. Set it as an environment variable:

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

Or modify the `nano_banana.py` file directly with your key.

## Commands

### generate
Generate an image from a text prompt.

```bash
figmaker generate "your prompt here" -o output.png [--aspect-ratio RATIO]
```

**Options:**
- `-o, --output`: Output file path (default: generated_image.png)
- `--aspect-ratio`: Image aspect ratio (e.g., 16:9, 1:1, 9:16)

### generate-only
Generate an image without any text response.

```bash
figmaker generate-only "your prompt here" -o output.png
```

### edit
Edit an existing image based on a text prompt.

```bash
figmaker edit input.jpg "edit description" -o output.png
```

**Arguments:**
- `image`: Path to input image
- `prompt`: Text description of the edits to make
- `-o, --output`: Output file path (default: edited_image.png)

## Examples

```bash
# Create a restaurant scene
figmaker generate "nano banana dish in a fancy restaurant" -o dish.png

# Portrait with specific aspect ratio
figmaker generate "portrait of an elderly ceramicist" --aspect-ratio 16:9 -o portrait.png

# Edit an existing photo
figmaker edit cat.jpg "add a small wizard hat on its head" -o wizard_cat.png

# Generate a transparent sticker
figmaker generate-only "cute red panda sticker with transparent background" -o sticker.png
```

## Requirements

- Python 3.8+
- google-genai >= 1.45.0
- pillow >= 12.0.0

## License

MIT License
