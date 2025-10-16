from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-code-validator",
    version="0.1.0",
    author="AI Code Validator Contributors",
    description="Catch AI-generated code mistakes before they cause problems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ai-code-validator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.1.0",
        "requests>=2.31.0",
        "colorama>=0.4.6",
        "GitPython>=3.1.40",
    ],
    entry_points={
        "console_scripts": [
            "aivalidate=ai_code_validator.cli:main",
        ],
    },
)
