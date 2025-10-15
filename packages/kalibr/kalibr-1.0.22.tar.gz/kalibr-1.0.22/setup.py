from setuptools import setup, find_packages

setup(
    name="kalibr",
    version="1.0.22",
    author="Kalibr Team",
    author_email="team@kalibr.dev",
    description="Multi-Model AI Integration Framework",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/devonakelley/kalibr-sdk",
    packages=find_packages(include=["kalibr", "kalibr.*"]),
    include_package_data=True,
    data_files=[
        ("examples", ["examples/basic_kalibr_example.py", "examples/enhanced_kalibr_example.py", "examples/README.md"]),
    ],
    install_requires=[
        "fastapi>=0.110.1",
        "uvicorn>=0.25.0",
        "pydantic>=2.6.4",
        "typer>=0.9.0",
        "requests>=2.31.0",
        "python-multipart>=0.0.9",
        "aiofiles>=23.2.1",
    ],
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "kalibr-connect=kalibr.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
