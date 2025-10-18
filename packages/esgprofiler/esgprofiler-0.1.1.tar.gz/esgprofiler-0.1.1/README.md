# ESGProfiler

🌍 **Automated ESG Scoring & Profiling with NLP and Open Data**

[![PyPI version](https://badge.fury.io/py/esgprofiler.svg)](https://pypi.org/project/esgprofiler/)

ESGProfiler is an open-source Python package and Streamlit dashboard for programmatically analyzing and visualizing the Environmental, Social, and Governance (ESG) signals for any company.

---

## Features

- 📈 **ESG Composite Scoring:** NLP-based analysis of annual reports, news, and filings to auto-compute ESG subscores (Environment, Social, Governance)
- 📰 **Flexible Data Ingestion:** Profile companies from Yahoo Finance, SEC filings, news headlines, report URLs, or custom-pasted text
- 🗺 **Streamlit Dashboard:** Interactive web app for quick analysis and ESG visualization
- ⚡ **Modular and Extensible:** Robust Python API for developers and researchers to adapt, plug in new data sources, and customize their workflow

---

## Quick Start

### 1. Install

pip install esgprofiler
python -m spacy download en_core_web_sm

text

### 2. Run Dashboard

esgprofiler-dashboard

text
Or for source builds:
streamlit run esgprofiler/dashboard.py

text

### 3. Use Python API

from esgprofiler.data_ingest import fetch_yahoo_profile, fetch_news_headlines
from esgprofiler.nlp_extract import count_esg_mentions
from esgprofiler.scoring import score_esg_text

profile = fetch_yahoo_profile("MSFT")
news = fetch_news_headlines("MSFT")
text = " ".join(news)
scores = score_esg_text(text)
print(scores)

text

---

## Dashboard Features

- Enter a company ticker or CIK
- Choose a data source: Yahoo News, SEC filing, report URL, or manual text
- See company profile and ESG scores
- Interactive breakdown by E/S/G
- Key signal sentences and expandable sections
- **NEW:** Copy/paste your own text or link to analyze custom data

---

## Project Structure

esgprofiler/
│ init.py
│ data_ingest.py
│ nlp_extract.py
│ scoring.py
│ config.py
│ dashboard.py
README.md
setup.py
requirements.txt
tests/
examples/

text

---

## Developer & Contribution Guide

- Fork and clone the repo
- Add features or suggestions via PRs and Issue tracker
- Extend keyword sets and weighting logic in `config.py`
- Package and dashboard designed for easy extension to global data (news APIs, non-US filings, etc.)

---

## License

MIT License © 2025 Your Name

---

## Acknowledgements

- [spaCy](https://spacy.io/)
- [Streamlit](https://streamlit.io/)
- [Yahoo Finance](https://finance.yahoo.com/)
- [SEC EDGAR](https://www.sec.gov/edgar.shtml)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)

---

## Disclaimer

This tool uses open/public data and simple NLP approaches. Scores are for demonstration and educational purposes only—do not use alone for serious investment decisions.