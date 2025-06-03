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
    {"year": 2026, "quarter": "Q1"},  # ended April 27, 2025
    {"year": 2025, "quarter": "Q4"},  # ended January 26, 2025
    {"year": 2025, "quarter": "Q3"},  # ended October 27, 2024
    {"year": 2025, "quarter": "Q2"},  # ended July 28, 2024
] # get_recent_nvda_quarters()

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
    prepared_remarks = []
    qna_section = []
    in_qna = False

    for segment in transcript:
        speaker_title = segment["title"].lower()
        content = segment["content"]

        # Detect start of Q&A based on analyst or operator introducing questions
        # This heuristic assumes Q&A starts once an "analyst" speaks or "operator" mentions "question" for the first time.
        if speaker_title == "analyst" or (speaker_title == "operator" and "question" in content.lower()):
            in_qna = True
        
        if in_qna:
            qna_section.append(content)
        # Only include CEO/CFO for prepared remarks before Q&A begins
        elif speaker_title in ["ceo", "cfo"]:
            prepared_remarks.append(content)
            
    return " ".join(prepared_remarks), " ".join(qna_section)

def analyze_sentiment(text: str, sentiment_analyzer) -> dict:
    """
    Analyzes the sentiment of a given text using a pre-trained sentiment analyzer.

    The sentiment score is calculated as the average positive score minus the average negative score.
    The label is determined based on predefined thresholds.

    Args:
        text (str): The input text to analyze.
        sentiment_analyzer: A callable sentiment analysis model (e.g., from Hugging Face pipelines)
                            that takes a list of sentences and returns a list of sentiment results
                            with 'label' (e.g., "POSITIVE", "NEGATIVE", "NEUTRAL") and 'score'.

    Returns:
        dict: A dictionary containing the sentiment 'label' and 'score'.
              Returns {"label": "NEUTRAL", "score": 0.0} if the text is empty.
    """
    if not text:
        return {"label": "NEUTRAL", "score": 0.0}
    
    # Tokenize the text into sentences for better granular analysis
    sentences = sent_tokenize(text)
    
    # Perform sentiment analysis on the sentences.
    # truncation=True and max_length=512 are common parameters for transformer models
    # to handle long inputs.
    results = sentiment_analyzer(sentences, truncation=True, max_length=512)
    
    # Extract scores for positive and negative sentiments
    positive_scores = [r["score"] for r in results if r["label"] == "POSITIVE"]
    negative_scores = [r["score"] for r in results if r["label"] == "NEGATIVE"]
    
    # Calculate the average score for positive and negative sentiments
    avg_positive_score = sum(positive_scores) / len(positive_scores) if positive_scores else 0
    avg_negative_score = sum(negative_scores) / len(negative_scores) if negative_scores else 0
    
    # Calculate the overall sentiment score (positive average - negative average)
    avg_score = avg_positive_score - avg_negative_score
    
    # Determine the sentiment label based on thresholds
    label = "POSITIVE" if avg_score > 0.1 else "NEGATIVE" if avg_score < -0.1 else "NEUTRAL"
    
    return {"label": label, "score": avg_score}

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
    # This helps to focus on more significant themes.
    themes = [word for word in keywords if word in word_counts and word_counts[word] > 2]
    
    # Return only the top N themes
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