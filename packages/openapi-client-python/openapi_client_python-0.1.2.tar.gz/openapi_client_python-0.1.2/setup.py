from setuptools import setup, find_packages

setup(
    name="openapi-client-python",
    version="0.1.2",
    author="autoocto",
    author_email="autoocto.ai@gmail.com",
    description="A tool to generate Python clients from OpenAPI specifications.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/autoocto/openapi-client-python",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "openapi-client-python=main:main",
        ],
    },
)