import streamlit as st
import requests
from textblob import TextBlob
import re
import numpy as np

st.set_page_config(page_title="📰 Fake News Credibility Scorer", layout="wide")
st.title("📰 Fake News Credibility Scorer")
st.markdown("Analyze news article credibility (0-100) with explainability")

def extract_features(title, content):
    """Extract NLP features from article"""
    full_text = title + " " + content
    blob = TextBlob(full_text)
    
    features = {
        "sentiment": blob.sentiment.polarity,
        "subjectivity": blob.sentiment.subjectivity,
        "length": len(content),
        "caps_ratio": sum(1 for c in content if c.isupper()) / len(content) if content else 0,
        "exclamation_count": content.count("!"),
        "entities": len([w for w in full_text.split() if w[0].isupper()]),
    }
    return features

def compute_credibility_score(features, source_domain=""):
    """Compute overall credibility 0-100"""
    # Content analysis (60%)
    content_score = 50  # baseline
    
    # High subjectivity = lower score
    content_score -= features["subjectivity"] * 20
    # Excessive capitals = suspicious
    content_score -= features["caps_ratio"] * 100 * 0.15
    # High exclamation marks = clickbait
    content_score -= min(features["exclamation_count"] / 3, 1) * 10
    # More entities = more credible
    content_score += min(features["entities"] / 20, 1) * 15
    
    content_score = max(0, min(100, content_score))
    
    # Source credibility (40%)
    source_score = 50  # baseline
    if source_domain:
        if any(trusted in source_domain for trusted in ["bbc", "reuters", "ap", "nyt"]):
            source_score = 90
        elif any(suspicious in source_domain for suspicious in ["blogspot", "medium"]):
            source_score = 40
        # Unknown sources neutral
    
    final_score = 0.6 * content_score + 0.4 * source_score
    return max(0, min(100, final_score))

col1, col2 = st.columns(2)
with col1:
    st.subheader("📝 Article Input")
    title = st.text_input("Article Title:")
    content = st.text_area("Article Content:", height=200)
with col2:
    st.subheader("🌐 Source Info")
    source_domain = st.text_input("Source Domain (e.g., bbc.com):")

if st.button("📊 Score Credibility") and title and content:
    features = extract_features(title, content)
    credibility = compute_credibility_score(features, source_domain)
    
    st.markdown("---")
    st.markdown("### 🎯 Credibility Score")
    
    if credibility > 75:
        color = "🟢"
        label = "LIKELY RELIABLE"
    elif credibility > 50:
        color = "🟡"
        label = "MIXED SIGNALS"
    else:
        color = "🔴"
        label = "LIKELY UNRELIABLE"
    
    st.metric(label, f"{credibility:.0f}/100", delta=f"{color}")
    st.progress(credibility / 100)
    
    st.markdown("### 🔍 Feature Analysis")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Sentiment", f"{features['sentiment']:.2f}", help="(-1: negative, +1: positive)")
    col2.metric("Subjectivity", f"{features['subjectivity']:.2f}", help="(0: factual, 1: opinionated)")
    col3.metric("Caps Ratio", f"{features['caps_ratio']:.1%}")
    col4.metric("Entities", f"{features['entities']}")
    
    st.markdown("### 💡 Factors Affecting Score")
    st.info(f"✅ Content Length: {features['length']} chars (good detail)")
    if features["subjectivity"] > 0.7:
        st.warning("❌ High subjectivity detected — mostly opinions, not facts")
    if features["caps_ratio"] > 0.1:
        st.warning("❌ Excessive capitalization — clickbait indicator")
    if features["exclamation_count"] > 3:
        st.warning(f"❌ {features['exclamation_count']} exclamation marks — sensationalism")
