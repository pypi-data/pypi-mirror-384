import spacy
from collections import defaultdict
import re

# Load small SpaCy English model; for more advanced NLP use transformers
nlp = spacy.load("en_core_web_sm")

# Example ESG keyword lists (to be expanded in config.py)
E_KEYWORDS = ["emissions", "waste", "renewable", "pollution", "carbon", "energy efficiency"]
S_KEYWORDS = ["diversity", "inclusion", "community", "donation", "charity", "well-being"]
G_KEYWORDS = ["board", "audit", "compliance", "transparency", "anti-corruption", "governance"]

def count_esg_mentions(text, e_keywords=E_KEYWORDS, s_keywords=S_KEYWORDS, g_keywords=G_KEYWORDS):
    """
    Returns the number of keyword hits for E, S, G in the given text.
    """
    counts = {"environment": 0, "social": 0, "governance": 0}
    text_lower = text.lower()
    for word in e_keywords:
        counts["environment"] += len(re.findall(rf"\b{word.lower()}\b", text_lower))
    for word in s_keywords:
        counts["social"] += len(re.findall(rf"\b{word.lower()}\b", text_lower))
    for word in g_keywords:
        counts["governance"] += len(re.findall(rf"\b{word.lower()}\b", text_lower))
    return counts

def extract_key_sentences(text, keywords, max_sentences=5):
    """
    Extract sentences containing any of the provided keywords.
    """
    doc = nlp(text)
    found = []
    for sent in doc.sents:
        sent_text = sent.text.lower()
        if any(kw.lower() in sent_text for kw in keywords):
            found.append(sent.text.strip())
        if len(found) >= max_sentences:
            break
    return found

def summarize_esg_signals(text):
    """
    Quick summary: extract a few representative sentences for E, S, and G.
    """
    e_sents = extract_key_sentences(text, E_KEYWORDS)
    s_sents = extract_key_sentences(text, S_KEYWORDS)
    g_sents = extract_key_sentences(text, G_KEYWORDS)
    return {
        "environment_sentences": e_sents,
        "social_sentences": s_sents,
        "governance_sentences": g_sents
    }
