from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="imagebreak",
    version="1.0.0",
    author="ImageBreak Contributors",
    author_email="ardada2468@gmail.com",
    description="A comprehensive framework for testing AI model safety and content moderation systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ardada2468/imagebreak",
    project_urls={
        "Bug Reports": "https://github.com/ardada2468/imagebreak/issues",
        "Source": "https://github.com/ardada2468/imagebreak",
        "Documentation": "https://github.com/ardada2468/imagebreak#readme",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Security",
        "Topic :: Software Development :: Testing",
    ],
    keywords="ai safety, content moderation, image generation, openai, dalle, boundary testing",
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "isort>=5.0",
        ],
        "aws": [
            "boto3>=1.26.0",
        ],
        "full": [
            "boto3>=1.26.0",
            "torch",
            "torchvision", 
            "transformers",
            "accelerate",
        ],
    },
    entry_points={
        "console_scripts": [
            "imagebreak=imagebreak.cli.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 