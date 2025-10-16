from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="simplation",
    version="1.0.3",
    author="Mohamed Gueni",
    author_email="mohamedgueni@outlook.com",
    description="A powerful command-line tool for analyzing and visualizing simulation data from CSV files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Gueni/simplation",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "colorama>=0.4.6",
        f"numpy>=2.0.0",
        "pandas>=2.2.2",
        "pyfiglet>=1.0.3",
        "rich>=14.0.0",
        "matplotlib>=3.6.2",
    ],
    entry_points={
        "console_scripts": [
            "simplation=simplation.cli:main",
        ],
    },
    keywords="simulation, data-analysis, csv, engineering, visualization, statistics",
    project_urls={
        "Bug Reports": "https://github.com/Gueni/simplation/issues",
        "Source": "https://github.com/Gueni/simplation",
        "Documentation": "https://github.com/Gueni/simplation#readme",
    },
)