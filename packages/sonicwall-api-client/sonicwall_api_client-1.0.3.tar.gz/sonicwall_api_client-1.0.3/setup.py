from setuptools import setup, find_packages

setup(
    name="sonicwall-api-client",
    version="1.0.3",
    author="Samuel Berset",
    author_email="your.email@example.com",
    description="Simple Python client for SonicWall SonicOS REST API (with HTTP Digest Auth).",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Samuel-Berset/sonicwall-api-client",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: System :: Networking",
    ],
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.25",
        "urllib3>=1.26",
    ],
    include_package_data=True,
)
