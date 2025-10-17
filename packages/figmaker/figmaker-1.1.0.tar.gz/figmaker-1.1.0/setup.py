from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="figmaker",
    version="1.1.0",
    description="AI-powered image generation and editing CLI tool using Gemini Nano Banana API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="FigMaker",
    author_email="",
    url="https://github.com/yourusername/figmaker",
    py_modules=["nano_banana"],
    install_requires=[
        "google-genai>=1.45.0",
        "pillow>=12.0.0",
    ],
    entry_points={
        "console_scripts": [
            "figmaker=nano_banana:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Graphics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.8",
    keywords="ai image generation editing gemini cli",
    license="MIT",
)
