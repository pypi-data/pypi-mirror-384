# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="malayalam-hate-detector",
    version="1.0.1",  # Increment version!
    author="Your Name",
    author_email="your.email@example.com",
    description="Advanced Malayalam Hate Speech Detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),  # ← THIS FINDS THE malayalam_hate_detector FOLDER
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License", 
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.7",
    install_requires=[
        "speechrecognition>=3.8.1",
        "transformers>=4.20.0",
        "torch>=1.12.0",
        "pyaudio>=0.2.11"
    ],
)