import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from transformers import pipeline
import nltk
from nltk.tokenize import sent_tokenize
from collections import Counter
import re

load_dotenv()

def get_recent_nvda_quarters(n: int = 4) -> list[dict]:
    today = datetime.today()
    year = today.year
    month = today.month

    # Map real month to NVDA fiscal quarter
    if month in [2, 3, 4]:
        fiscal_quarter = "Q1"
    elif month in [5, 6, 7]:
        fiscal_quarter = "Q2"
    elif month in [8, 9, 10]:
        fiscal_quarter = "Q3"
    else:  # 11, 12, 1
        fiscal_quarter = "Q4"
        if month == 1:
            year -= 1  # Jan is part of Q4 of previous fiscal year

    # Create list of quarters
    quarter_order = ["Q4", "Q3", "Q2", "Q1"]
    index = quarter_order.index(fiscal_quarter)
    
    quarters = []
    for _ in range(n):
        q = quarter_order[index]
        quarters.append({"year": year, "quarter": q})
        index -= 1
        if index < 0:
            index = 3
            year -= 1

    return quarters

STOCK_API_KEY = os.getenv("STOCK_API_KEY", "")
STOCK_END_POINT = "https://www.alphavantage.co/query"
SYMBOL = "NVDA"
QUARTERS = [
    {"year": 2026, "quarter": "Q1"},  # ended April 27, 2025
    {"year": 2025, "quarter": "Q4"},  # ended January 26, 2025
    {"year": 2025, "quarter": "Q3"},  # ended October 27, 2024
    {"year": 2025, "quarter": "Q2"},  # ended July 28, 2024
] # get_recent_nvda_quarters()

# Download NLTK data
nltk.download('punkt_tab')


def get_data(year: int, quarter: str) -> dict:
    nvda_params = {
        'function': 'EARNINGS_CALL_TRANSCRIPT',
        'symbol': SYMBOL,
        'quarter': f"{year}{quarter}",
        'apikey': STOCK_API_KEY,
    }
    response = requests.get(STOCK_END_POINT, nvda_params)
    response.raise_for_status()
    data = response.json()
    return data

def extract_sections(transcript: list[dict]) -> tuple[str, str]:
    prepared = []
    qna = []
    in_qna = False
    for segment in transcript:
        speaker_title = segment["title"].lower()
        content = segment["content"]
        # Detect start of Q&A based on analyst or operator introducing questions
        if speaker_title == "analyst" or (speaker_title == "operator" and "question" in content.lower()):
            in_qna = True
        if in_qna:
            qna.append(content)
        elif speaker_title in ["ceo", "cfo"]:  # Only include CEO/CFO for prepared remarks
            prepared.append(content)
    return " ".join(prepared), " ".join(qna)

def analyze_sentiment(text: str, sentiment_analyzer) -> dict:
    if not text:
        return {"label": "NEUTRAL", "score": 0.0}
    sentences = sent_tokenize(text)
    results = sentiment_analyzer(sentences, truncation=True, max_length=512)
    positive_scores = [r["score"] for r in results if r["label"] == "POSITIVE"]
    negative_scores = [r["score"] for r in results if r["label"] == "NEGATIVE"]
    avg_score = sum(positive_scores) / len(positive_scores) if positive_scores else 0
    avg_score -= sum(negative_scores) / len(negative_scores) if negative_scores else 0
    label = "POSITIVE" if avg_score > 0.1 else "NEGATIVE" if avg_score < -0.1 else "NEUTRAL"
    return {"label": label, "score": avg_score}

def extract_themes(transcript: list[dict], top_n: int = 5) -> list[str]:
    keywords = [
        "AI", "artificial intelligence", "data center", "growth", "revenue",
        "innovation", "technology", "GPU", "cloud", "partnerships",
        "Blackwell", "Hopper", "Sovereign AI", "inference", "training", "CUDA",
        "RTX", "DLSS", "Omniverse", "edge computing", "AI chips", "deep learning",
        "neural networks", "accelerator", "chips", "semiconductors", "autonomous vehicles",
        "gaming", "metaverse", "GPU architecture", "Ray tracing","Tensor cores", "NVLink",
        "DGX systems", "robotics", "AI supercomputer", "H100", "A100", "Jetson", "shield",
        "virtual reality", "smart NIC", "NVIDIA AI Enterprise", "Maxine", "climate modeling",
        "AI inference", "AI training", "partnerships", "chip design", "supply chain", "silicon",
    ]
    text = " ".join(segment["content"] for segment in transcript).lower()
    words = re.findall(r'\b\w+\b', text)
    word_counts = Counter(words)
    themes = [word for word in keywords if word in word_counts and word_counts[word] > 2]
    return themes[:top_n]

def main() -> None:
    # Initialize sentiment analyzer
    sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    
    #Step 1: Automatically identify and retrieve full transcripts of NVIDIA’s earnings calls for the last four quarters.
    transcripts = []
    for q in QUARTERS:
        year = q["year"]
        quarter = q["quarter"]
        a = get_data(year, quarter)
        transcripts.append(a)
    
    # Step 2: Signal extraction
    results = []
    for transcript in transcripts:
        quarter_str = transcript.get("quarter", "")  # e.g. "2025Q1"
        year, quarter = quarter_str[:4], quarter_str[4:]
        segments = transcript.get("transcript", [])

        if not segments:
            print(f"Warning: No transcript data for {year} {quarter}")
            continue

        prepared, qna = extract_sections(segments)

        # Management Sentiment: Overall sentiment (positive/neutral/negative) of prepared remarks by executives.
        management_sentiment = analyze_sentiment(prepared, sentiment_analyzer)

        # Q&A Sentiment: Overall tone and sentiment during the Q&A portion.
        qna_sentiment = analyze_sentiment(qna, sentiment_analyzer)

        #  Strategic Focuses: Extract 3-5 key themes or initiatives emphasized each quarter (e.g., AI growth, data center expansion).
        themes = extract_themes(segments)

        results.append({
            "year": year,
            "quarter": quarter,
            "management_sentiment": management_sentiment,
            "qna_sentiment": qna_sentiment,
            "themes": themes
        })

    #  Quarter-over-Quarter Tone Change: Analyze and compare sentiment/tone shifts across the four quarters.
    print("\nQuarterly Analysis:")
    for i, result in enumerate(results):
        print(f"\n{result['year']} {result['quarter']}:")
        print(f"  Management Sentiment: {result['management_sentiment']['label']} (Score: {result['management_sentiment']['score']:.2f})")
        print(f"  Q&A Sentiment: {result['qna_sentiment']['label']} (Score: {result['qna_sentiment']['score']:.2f})")
        print(f"  Strategic Themes: {', '.join(result['themes'])}")

        # Compare with previous quarter
        if i > 0:
            prev = results[i - 1]
            mgmt_score_diff = result["management_sentiment"]["score"] - prev["management_sentiment"]["score"]
            qna_score_diff = result["qna_sentiment"]["score"] - prev["qna_sentiment"]["score"]

            print(f"  Tone Change (vs {prev['year']} {prev['quarter']}):")
            print(f"    Management: {'More positive' if mgmt_score_diff > 0 else 'More negative' if mgmt_score_diff < 0 else 'Stable'} ({mgmt_score_diff:.2f})")
            print(f"    Q&A: {'More positive' if qna_score_diff > 0 else 'More negative' if qna_score_diff < 0 else 'Stable'} ({qna_score_diff:.2f})")

    
    #Step 3: User Interface
    
    
    #Step 4: Deploy

if __name__ == "__main__":
    main()