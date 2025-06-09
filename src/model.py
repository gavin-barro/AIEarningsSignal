import os
import requests
from datetime import datetime
from typing import Any
from dotenv import load_dotenv
from transformers import pipeline
import nltk
from nltk.tokenize import sent_tokenize
from collections import Counter
import re

load_dotenv()

def get_recent_nvda_quarters(n: int = 4) -> list[dict]:
    """
    Calculates and returns a list of NVIDIA's most recent fiscal quarters.

    NVIDIA's fiscal year ends in January, meaning their fiscal quarters do not
    directly align with calendar quarters. This function determines the current
    fiscal quarter and then counts backward `n` quarters.

    Args:
        n (int): The number of recent quarters to retrieve. Defaults to 4.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents a
                    fiscal quarter with its 'year' and 'quarter' (e.g., {"year": 2025, "quarter": "Q1"}).
    """
    today = datetime.today()
    year = today.year
    month = today.month

    # Map real month to NVDA fiscal quarter based on their fiscal year end in January
    if month in [2, 3, 4]:  # Feb, Mar, Apr
        fiscal_quarter = "Q1"
    elif month in [5, 6, 7]:  # May, Jun, Jul
        fiscal_quarter = "Q2"
    elif month in [8, 9, 10]:  # Aug, Sep, Oct
        fiscal_quarter = "Q3"
    else:  # Nov, Dec, Jan
        fiscal_quarter = "Q4"
        # If the current month is January, it belongs to Q4 of the *previous* fiscal year
        if month == 1:
            year -= 1

    # Define the order of fiscal quarters to facilitate counting backward
    quarter_order = ["Q4", "Q3", "Q2", "Q1"]
    # Get the index of the current fiscal quarter in the ordered list
    index = quarter_order.index(fiscal_quarter)
    
    quarters = []
    # Iterate `n` times to get the desired number of recent quarters
    for _ in range(n):
        q = quarter_order[index]
        quarters.append({"year": year, "quarter": q})
        
        # Move to the previous quarter
        index -= 1
        # If we go past Q1 (index becomes -1), wrap around to Q4 and decrement the year
        if index < 0:
            index = 3  # Q4 is at index 3
            year -= 1

    return quarters

STOCK_API_KEY = os.getenv("STOCK_API_KEY", "")
STOCK_END_POINT = "https://www.alphavantage.co/query"
SYMBOL = "NVDA"
QUARTERS = [
    {"year": 2025, "quarter": "Q1"},
    {"year": 2024, "quarter": "Q4"},
    {"year": 2024, "quarter": "Q3"},
    {"year": 2024, "quarter": "Q2"},
] 

# Download NLTK data
nltk.download('punkt_tab')

def get_data(year: int, quarter: str) -> dict:
    """
    Fetches the earnings call transcript for a specified NVIDIA fiscal quarter from Alpha Vantage.

    Args:
        year (int): The fiscal year (e.g., 2025).
        quarter (str): The fiscal quarter (e.g., "Q1", "Q2", "Q3", "Q4").

    Returns:
        dict: The JSON response containing the earnings call transcript data.

    Raises:
        requests.exceptions.HTTPError: If the API request returns an unsuccessful status code.
    """
    nvda_params = {
        'function': 'EARNINGS_CALL_TRANSCRIPT',
        'symbol': SYMBOL,
        # Alpha Vantage expects quarter in 'YYYYQN' format (e.g., "2025Q1")
        'quarter': f"{year}{quarter}", 
        'apikey': STOCK_API_KEY,
    }
    response = requests.get(STOCK_END_POINT, nvda_params)
    response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
    data = response.json()
    return data

def extract_sections(transcript: list[dict]) -> tuple[str, str]:
    """
    Extracts and separates the prepared remarks and Q&A sections from an earnings call transcript.

    Prepared remarks are typically from CEO/CFO, and the Q&A section starts when an
    analyst or the operator begins asking questions.

    Args:
        transcript (list[dict]): A list of dictionaries, where each dictionary represents
                                 a segment of the transcript with 'title' (speaker role)
                                 and 'content'.

    Returns:
        tuple[str, str]: A tuple containing two strings:
                         - The concatenated text of the prepared remarks.
                         - The concatenated text of the Q&A section.
    """
    speaker_remarks = []
    qna_section = []

    for segment in transcript:
        speaker_title = segment["title"].lower()
        content = segment["content"]

        if speaker_title in ["ceo", "cfo"]:
            speaker_remarks.append(content)
        
        qna_section.append(content)
            
    return " ".join(speaker_remarks), " ".join(qna_section)

def analyze_sentiment(text: str, sentiment_analyzer: Any) -> dict:
    """
    Analyzes the sentiment of a given text using a pre-trained sentiment analyzer.

    Args:
        text (str): The input text to analyze.
        sentiment_analyzer: A callable sentiment analysis model (e.g., from Hugging Face pipelines)
                            that takes a list of sentences and returns a list of sentiment results
                            with 'label' (e.g., "POSITIVE", "NEUTRAL", "NEGATIVE") and 'score'.

    Returns:
        dict: A dictionary containing the sentiment 'label' and 'score'.
              Returns {"label": "NEUTRAL", "score": 0.0} if the text is empty.
    """
    if not text:
        return {"label": "NEUTRAL", "score": 0.0}
    
    # Tokenize the text into sentences for better granular analysis
    sentences = sent_tokenize(text)
    
    # Perform sentiment analysis on the sentences
    results = sentiment_analyzer(sentences, truncation=True, max_length=512)
    
    # Count occurrences of each label and average scores
    labels = [r["label"] for r in results]
    scores = [r["score"] for r in results]
    
    # Map labels to standard form
    label_map = {"NEG": "NEGATIVE", "NEU": "NEUTRAL", "POS": "POSITIVE"}
    mapped_labels = [label_map.get(label, label) for label in labels]
    
    # Calculate average score per label
    positive_scores = [s for s, l in zip(scores, mapped_labels) if l == "POSITIVE"]
    negative_scores = [s for s, l in zip(scores, mapped_labels) if l == "NEGATIVE"]
    neutral_scores = [s for s, l in zip(scores, mapped_labels) if l == "NEUTRAL"]
    
    avg_positive = sum(positive_scores) / len(positive_scores) if positive_scores else 0
    avg_negative = sum(negative_scores) / len(negative_scores) if negative_scores else 0
    avg_neutral = sum(neutral_scores) / len(neutral_scores) if neutral_scores else 0
    
    # Determine dominant label by frequency and average score
    label_counts = {"POSITIVE": len(positive_scores), "NEUTRAL": len(neutral_scores), "NEGATIVE": len(negative_scores)}
    max_count = max(label_counts.values())
    dominant_label = max(label_counts, key=lambda k: (label_counts[k], {"POSITIVE": avg_positive, "NEUTRAL": avg_neutral, "NEGATIVE": avg_negative}[k]))
    
    # Use the average score of the dominant label
    score = {"POSITIVE": avg_positive, "NEUTRAL": avg_neutral, "NEGATIVE": avg_negative}[dominant_label]
    
    return {"label": dominant_label, "score": score}

def extract_themes(transcript: list[dict], top_n: int = 5) -> list[str]:
    """
    Extracts recurring themes (keywords) from an earnings call transcript.

    It uses a predefined list of NVIDIA-specific keywords and counts their occurrences
    across the entire transcript. Themes with more than 2 occurrences are considered.

    Args:
        transcript (list[dict]): A list of dictionaries, where each dictionary represents
                                 a segment of the transcript with 'content'.
        top_n (int): The maximum number of top themes to return. Defaults to 5.

    Returns:
        list[str]: A list of relevant keywords/themes found in the transcript,
                   limited to `top_n`.
    """
    # Define a comprehensive list of NVIDIA-related keywords and themes
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
    
    # Concatenate all content into a single string and convert to lowercase for case-insensitive matching
    text = " ".join(segment["content"] for segment in transcript).lower()
    
    # Find all word tokens in the text
    words = re.findall(r'\b\w+\b', text)
    
    # Count the frequency of each word
    word_counts = Counter(words)
    
    # Filter keywords that are present in the transcript and appear more than twice
    themes = [word for word in keywords if word in word_counts and word_counts[word] > 2]
    
    # Return only the top N themes
    return themes[:top_n]

def ndva_analysis() -> list[dict]:
    # Initialize sentiment analyzer with a model that supports neutral sentiment
    sentiment_analyzer = pipeline("sentiment-analysis", model="finiteautomata/bertweet-base-sentiment-analysis")
    
    # Step 1: Automatically identify and retrieve full transcripts of NVIDIA’s earnings calls for the last four quarters.
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

        # Extract transcript segments without sentiment
        transcript_segments = [
            {
                "speaker": segment.get("speaker", "Unknown"),
                "title": segment.get("title", "Unknown"),
                "content": segment.get("content", "")
            }
            for segment in segments if segment.get("content", "")
        ]

        # Extract prepared remarks and Q&A sections
        executives, qna = extract_sections(segments)

        # Management Sentiment: Overall sentiment (positive/neutral/negative) of prepared remarks by executives.
        management_sentiment = analyze_sentiment(executives, sentiment_analyzer)

        # Q&A Sentiment: Overall tone and sentiment during the Q&A portion.
        qna_sentiment = analyze_sentiment(qna, sentiment_analyzer)

        # Strategic Focuses: Extract 3-5 key themes or initiatives emphasized each quarter.
        themes = extract_themes(segments)

        # Append results with transcript segments
        results.append({
            "year": year,
            "quarter": quarter,
            "management_sentiment": management_sentiment,
            "qna_sentiment": qna_sentiment,
            "themes": themes,
            "transcript": transcript_segments
        })

    return results

def print_score_diff(category: str, score_diff: float) -> None:
    if score_diff == 0:
        sentiment = "Stable"
    elif score_diff > 0:
        sentiment = "Slightly more positive" if score_diff < 0.1 else "More positive"
    else:
        sentiment = "Slightly more negative" if score_diff > -0.1 else "More negative"
    print(f"    {category}: {sentiment} ({score_diff:.2f})")

def main() -> None:
    results = ndva_analysis()
    
    # Quarter-over-Quarter Tone Change: Analyze and compare sentiment/tone shifts across the four quarters.
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
            print_score_diff("Management", mgmt_score_diff)
            print_score_diff("Q&A", qna_score_diff)

if __name__ == "__main__":
    main()