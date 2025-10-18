# ESGProfiler

**Automated ESG scoring and profiling for companies using Python and NLP.**

---

ESGProfiler is an open-source Python package and interactive Streamlit dashboard to help investors, analysts, and researchers quantitatively assess the Environmental, Social, and Governance (ESG) footprint of any company—based on public filings, news, and reports.

## Features

- 📊 **Automated ESG scoring**
    - Extract ESG metrics from text (filings, reports, news)
    - Compute subscores (Environment, Social, Governance) and composite ESG ratings
- 📰 **Data sourcing**
    - Ingest from Yahoo Finance, SEC filings, news headlines, report URLs, or pasted text
- 💬 **NLP-driven analysis**
    - Keyword analysis and key sentence extraction with spaCy & transformers
- 📈 **Streamlit dashboard**
    - Interactive, visual results. Upload documents, analyze companies, and compare ESG ratings.
- ⚡ **Modular, extensible package**
    - Easy for researchers to extend scoring, NLP, or data sources

## Quickstart

1. **Install dependencies**
    ```
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
    ```

2. **Install ESGProfiler**
    - From source:
      ```
      git clone https://github.com/yourusername/esgprofiler.git
      cd esgprofiler
      pip install .
      ```
    - Or use `pip install esgprofiler` (after PyPI release)

3. **Run the Streamlit dashboard**
    ```
    esgprofiler-dashboard
    ```
    Alternatively, from source:
    ```
    streamlit run esgprofiler/dashboard.py
    ```

4. **Python API usage**

    ```
    from esgprofiler.data_ingest import fetch_yahoo_profile, fetch_news_headlines
    from esgprofiler.nlp_extract import count_esg_mentions
    from esgprofiler.scoring import score_esg_text

    profile = fetch_yahoo_profile("AAPL")
    text = " ".join(fetch_news_headlines("AAPL"))
    results = score_esg_text(text)
    print(results)
    ```

## Project Structure

esgprofiler/
│ esgprofiler/
│ data_ingest.py
│ nlp_extract.py
│ scoring.py
│ config.py
│ dashboard.py
│ requirements.txt
│ README.md
│ setup.py
│ tests/
│ examples/



## Contribution & Extension

- Expand keyword lists and scoring strategies in `config.py`
- Add new data sources (global filings, sustainability reports)
- Replace rule-based NLP with advanced ML if desired
- PRs, suggestions, and issues are welcome!

## License

MIT License © 2025 [Advait Dharmadhikari]
