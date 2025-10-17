from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="speedbuild",
    version="0.1.6.9",
    description="Extracts, adapts, and deploys battle-tested features from existing codebases to new projects—complete with all dependencies, configurations, and framework integrations.",
    long_description=long_description,
    long_description_content_type="text/markdown",  # Required for README.md
    packages=find_packages(),
    install_requires=[
        "django",
        "pyyaml",
        "openai",
        "requests",
        "websockets",
        "langgraph",
        "langchain",
        "esprima",
        "rich",
        "langchain-openai"
    ],
    entry_points={
        'console_scripts': [
            'speedbuild=speedbuild.sb:start',
        ],
    },
)
