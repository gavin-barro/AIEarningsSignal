import os
import requests
from dotenv import load_dotenv

load_dotenv()

STOCK_API_KEY = os.getenv("STOCK_API_KEY", "")
STOCK_END_POINT = "https://www.alphavantage.co/query"
SYMBOL = "NVDA"
QUARTERS = [
    {"year": 2025, "quarter": "Q1"},  # Q1 2026 (ended April 2025)
    {"year": 2025, "quarter": "Q4"},  # Q4 2025 (ended January 2025)
    {"year": 2024, "quarter": "Q3"},  # Q3 2025 (ended October 2024)
    {"year": 2024, "quarter": "Q2"},  # Q2 2025 (ended July 2024)
]

def get_data(year: int, quarter: str):
    nvda_params = {
        'function': 'EARNINGS_CALL_TRANSCRIPT',
        'symbol': SYMBOL,
        'quarter': f"{year}{quarter}",
        'apikey': STOCK_API_KEY,
    }
    response = requests.get(STOCK_END_POINT, nvda_params)
    response.raise_for_status()
    data = response.json()
    print(data)

def main() -> None:
    #Step 1: Automatically identify and retrieve full transcripts of NVIDIA’s earnings calls for the last four quarters.
    transcripts = []
    for q in QUARTERS:
        year = q["year"]
        quarter = q["quarter"]
        transcripts.append(get_data(year, quarter))
    
    #Step 2: Signal extraction
    
    
    #Step 3: User Interface
    
    
    #Step 4: Deploy

if __name__ == "__main__":
    main()