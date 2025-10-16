from setuptools import setup, find_packages

setup(
    name="Maxmodule",  # must be unique on PyPI
    version="0.0.3",
    packages=find_packages(),
    description="A simple example Python module",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Max",
    author_email="your-email@example.com",
    url="https://github.com/yourusername/mymodule",  # optional
    license="MIT",
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)