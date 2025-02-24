from setuptools import setup, find_packages


setup(
    name="pyjector",
    version="0.1.0",
    description="A lightweight Dependency Injection container for Python",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Sa(n)d",
    author_email="oesand@github.com",
    url="https://github.com/oesand/pyjector",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
    ],
    python_requires=">=3.7",
)
