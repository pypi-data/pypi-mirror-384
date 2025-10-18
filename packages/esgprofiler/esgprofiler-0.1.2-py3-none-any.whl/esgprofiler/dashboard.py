import streamlit as st
# Import the data_ingest module and resolve functions dynamically to avoid an import-time error
# if an optional function (like fetch_news_headlines) is not present.
try:
    import esgprofiler.data_ingest as _data_ingest
except ImportError:
    _data_ingest = None

if _data_ingest:
    fetch_yahoo_profile = getattr(_data_ingest, "fetch_yahoo_profile", lambda ticker: {})
    fetch_sec_filings = getattr(_data_ingest, "fetch_sec_filings", lambda ticker: [])
    fetch_url_text = getattr(_data_ingest, "fetch_url_text", lambda url: "")
    fetch_news_headlines = getattr(_data_ingest, "fetch_news_headlines", lambda ticker: [])
else:
    # Minimal fallbacks so the dashboard can still run when the package is not available.
    def fetch_yahoo_profile(ticker):
        return {}
    def fetch_sec_filings(ticker):
        return []
    def fetch_url_text(url):
        return ""
    def fetch_news_headlines(ticker):
        return []

from esgprofiler.nlp_extract import count_esg_mentions, summarize_esg_signals
from esgprofiler.scoring import aggregate_esg_counts, compute_overall_esg_score, score_esg_text
from esgprofiler.config import get_default_keywords, get_sector_weights
import pandas as pd

st.set_page_config(
    page_title="ESGProfiler Dashboard",
    page_icon="🌍",
    layout="wide",
)

def main():
    st.title("🌍 ESGProfiler: Automated ESG Scoring Dashboard")
    st.markdown("""
        **Welcome!**
        Analyze the environmental, social, and governance (ESG) profile of companies using NLP and multiple data sources.
        - Select a company, choose how you want to analyze it, and visualize ESG signals.
        - *Tip: If news headlines do not load, paste your own text/report for demoing ESG scoring.*
    """)

    st.sidebar.header("Options")
    ticker = st.sidebar.text_input("Enter Company Ticker/Symbol (e.g., MSFT, TSLA, AAPL):")
    source = st.sidebar.selectbox(
        "Choose Data Source",
        ["Yahoo Profile & News", "SEC Filing (US only)", "Paste Report URL", "Paste Raw Text"],
    )
    st.sidebar.info("🔎 Try using 'Paste Report URL' or 'Raw Text' for custom inputs.")

    if ticker:
        st.header(f"Analysis for: {ticker}")
        profile = fetch_yahoo_profile(ticker)
        with st.expander("Company Quick Profile", expanded=True):
            st.json(profile or {"Error": "No profile data found."})
        sector = profile.get("sector", "")
        weights = get_sector_weights(sector)
        config = get_default_keywords()
        config["weights"] = weights

        # Text Ingestion
        text = ""
        note = ""
        if source == "Yahoo Profile & News":
            news_list = fetch_news_headlines(ticker)
            if not news_list:
                note = "No recent headlines found, news provider may have changed. Try another option!"
            text = " ".join(news_list)
            with st.expander("News Headlines Used"):
                if news_list:
                    st.write(pd.DataFrame({"Headline": news_list}))
                else:
                    st.info(note)
            st.write(f"📰 Used {len(news_list)} headlines.")
        elif source == "SEC Filing (US only)":
            files = fetch_sec_filings(ticker)
            if files:
                with open(files[0], encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                st.info(f"Loaded SEC filing: {files[0]}")
            else:
                st.error("No SEC filings found. Try another data source.")
        elif source == "Paste Report URL":
            url = st.text_input("🔗 Enter Public Report URL (PDF or HTML):")
            if url:
                text = fetch_url_text(url)
                st.success("Report loaded from URL!")
            else:
                st.warning("Enter a valid URL above.")
        elif source == "Paste Raw Text":
            text = st.text_area("Paste company report, news, or sustainability narrative here:")
            if not text.strip():
                st.warning("Paste text above to analyze.")

        # ESG Analysis
        if text.strip():
            st.header("✨ ESG Signal Summary")
            counts = count_esg_mentions(
                text,
                config["environment_keywords"],
                config["social_keywords"],
                config["governance_keywords"],
            )
            subscores = aggregate_esg_counts(counts)
            overall = compute_overall_esg_score(subscores, weights)

            # Display ESG Composite and Subscores
            st.metric("🌍 ESG Composite Score", f"{overall}/100")
            st.write("Environmental:", subscores["environment_score"])
            st.write("Social:", subscores["social_score"])
            st.write("Governance:", subscores["governance_score"])
            st.info("Scores are based on frequency and context of keywords found in provided data.")

            # Show Breakdown
            summary = summarize_esg_signals(text)
            with st.expander("Environmental Signal Sentences"):
                for sent in summary["environment_sentences"]:
                    st.write("•", sent)
            with st.expander("Social Signal Sentences"):
                for sent in summary["social_sentences"]:
                    st.write("•", sent)
            with st.expander("Governance Signal Sentences"):
                for sent in summary["governance_sentences"]:
                    st.write("•", sent)
        else:
            st.warning("No analysis performed. Provide valid input data to score ESG signals.")

    st.caption("© 2025 ESGProfiler | Open-source finance analytics | Advait Dharmadhikari")

if __name__ == "__main__":
    main()
# (removed duplicate implementation; the working fetch_news_headlines is defined further below)