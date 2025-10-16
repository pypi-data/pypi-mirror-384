from setuptools import setup, find_packages

setup(
    name="malayalam-hate-detector",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "speechrecognition>=3.8.1",
        "transformers>=4.20.0",
        "torch>=1.12.0",
        "pyaudio>=0.2.11"
    ],
    author="Your AI Solutions",
    author_email="contact@yourai.com",
    description="Advanced Malayalam Hate Speech Detection using proprietary AI models",
    long_description="A sophisticated AI system for real-time Malayalam hate speech detection from speech and text inputs.",
    long_description_content_type="text/markdown",
    keywords="malayalam hate speech detection ai nlp machine learning",
    url="https://github.com/jubin217/malayalam-hate-detector",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
)