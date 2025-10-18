from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="esgprofiler",  # Change if this is taken on PyPI
    version="0.1.1",
    author="Advait Dharmadhikari",
    author_email="advaituni@gmail.com",
    description="Automated ESG scoring and profiling for companies using NLP and open data sources.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/advait27/ESGProfiler.git", 
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "pandas",
        "numpy",
        "requests",
        "beautifulsoup4",
        "yfinance",
        "scikit-learn",
        "spacy",
        "transformers",
        "sec-edgar-downloader",
        "plotly"
    ],
    entry_points={
        "console_scripts": [
            "esgprofiler-dashboard=esgprofiler.dashboard:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial",
        "Natural Language :: English",
        "Development Status :: 3 - Alpha"
    ],
    python_requires=">=3.11",
    include_package_data=True,
    license="MIT",
    project_urls={
        "Documentation": "https://github.com/advait27/ESGProfiler.git",
        "Source": "https://github.com/advait27/ESGProfiler.git",
        "Bug Tracker": "https://github.com/advait27/ESGProfiler.git/issues",
    }
)
