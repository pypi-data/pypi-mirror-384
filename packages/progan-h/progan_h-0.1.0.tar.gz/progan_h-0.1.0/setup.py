from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="progan-h",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A CLI tool to provide documentation and examples for machine learning algorithms",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/progan-h",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "click>=8.0.0",
        "rich>=10.0.0",
        "markdown>=3.3.0",
    ],
    entry_points={
        "console_scripts": [
            "progan-h=progan_h.cli:main",
        ],
    },
    package_data={
        "progan_h": ["docs/*.md"],
    },
    include_package_data=True,
)
