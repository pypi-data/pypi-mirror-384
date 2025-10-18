from setuptools import setup, find_packages

setup(
    name="esgprofiler",
    version="0.1.0",
    description="Automated ESG scoring and profiling engine for companies",
    author="Advait Dharmadhikari",
    author_email="advaituni@gmail.com",
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
    python_requires=">=3.11",
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "esgprofiler-dashboard=esgprofiler.dashboard:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3.13",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
