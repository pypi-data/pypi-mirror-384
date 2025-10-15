from setuptools import setup, find_packages

setup(
    name="eldar-fancy-text-matrix",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["colorama"],
    python_requires=">=3.10",
    author="Eldar Eliyev",
    description="Emoji fancy text generator",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/eldareliy/fancy_text",  # öz repo linkin
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
