from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dumprx",
    version="2.0.0",
    author="DumprX Team",
    author_email="dumprx@example.com",
    description="Modern Python firmware dumping and extraction toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Eduardob3677/DumprX",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "rich>=13.0.0",
        "requests>=2.25.0",
        "pathlib2>=2.3.0",
    ],
    entry_points={
        "console_scripts": [
            "dumprx=dumprx.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "dumprx": ["bin/*", "utils/*"],
    },
)