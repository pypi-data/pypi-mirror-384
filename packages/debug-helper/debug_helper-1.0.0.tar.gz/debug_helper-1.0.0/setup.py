from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="debug-helper",
    version="1.0.0",
    author="Debug Helper Team",
    author_email="support@debughelper.com",
    description="A production-grade debugging and issue tracking helper SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/debug-helper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Debuggers",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
    },
    entry_points={
        "console_scripts": [
            "debug-helper=debug_helper.cli:main",
        ],
    },
)