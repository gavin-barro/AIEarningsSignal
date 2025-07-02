# NVIDIA Earnings Sentiment Analyzer

This web application analyzes quarterly earnings call transcripts from NVIDIA to extract insights about management tone, Q&A sentiment, and strategic themes. It helps investors and analysts quickly assess the emotional tone and priorities of company leadership over recent fiscal quarters.

## Author
Gavin Barro

## What the App Does
- Fetches and processes NVIDIA’s earnings call transcripts (via Alpha Vantage).
- Applies sentiment analysis on:
  - Prepared remarks (by CEO/CFO).
  - Q&A session (from analysts/investors).
- Extracts strategic themes based on keyword frequency.
- Visualizes trends in management vs. Q&A sentiment over time using Chart.js.
- You can run the analysis manually via CLI or view the results through a Flask-based web dashboard.

## How to Run It Locally
1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/nvda-sentiment-app.git
   cd nvda-sentiment-app
   ```
2. **Set Up Environment**
   - Create a `.env` file and add your Alpha Vantage API key:
     ```ini
     STOCK_API_KEY=your_alpha_vantage_key_here
     ```
   - Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - Dependencies include: Flask, requests, transformers, nltk, python-dotenv
   - Download required NLTK models:
     ```bash
     python -m nltk.downloader punkt
     ```
3. **Run the Flask App**
   ```bash
   python app.py
   ```
   - Navigate to `http://127.0.0.1:5000/` to see the dashboard.

## AI / NLP Tools Used
- ** Hugging Face Transformers**:
  - Model: `finiteautomata/bertweet-base-sentiment-analysis` (supports positive, neutral, and negative sentiment).
- **NLTK**: Sentence tokenization for better sentiment granularity.
- **Custom Theme Extraction**: Uses a curated set of NVIDIA-specific keywords and counts frequency across transcripts.
- **Alpha Vantage API**: Supplies the earnings call transcript data.

## 📁 File Overview
```
.
├── .gitignore
├── live_link.txt
├── README.md
├── src/
│   ├── app.py
│   ├── model.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── css/
│       │   └── style.css
│       ├── img/
│       └── js/
│           └── script.js
├── .env
```
