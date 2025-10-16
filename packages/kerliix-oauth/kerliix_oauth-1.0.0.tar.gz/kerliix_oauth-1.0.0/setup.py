from setuptools import setup, find_packages

setup(
    name="kerliix-oauth",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
    ],
    python_requires=">=3.9",
    url="https://github.com/kerliix-corp/kerliix-oauth-python",
    author="Kerliix Corporation",
    author_email="dev@kerliix.com",
    description="Kerliix OAuth 2.0 SDK for Python",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
