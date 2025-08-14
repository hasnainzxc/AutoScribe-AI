from setuptools import setup, find_packages

setup(
    name="content_pipeline",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "praw",  # for Reddit API
        "python-dotenv",  # for loading environment variables
    ],
)
