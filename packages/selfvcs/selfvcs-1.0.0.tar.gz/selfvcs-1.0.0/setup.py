from setuptools import setup, find_packages
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
setup(
    name="selfvcs",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="GitHub-like version control system with AI-powered auto-updates",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/codevault",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "groq>=0.4.0",
    ],
    entry_points={
        "console_scripts": [
            "codevault=codevault.cli:main",
        ],
    },
    include_package_data=True,
)