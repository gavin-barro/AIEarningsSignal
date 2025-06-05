from flask import Flask, render_template
from model import ndva_analysis

app = Flask(__name__)

@app.route('/')
def index():
    # Switch to ndva_analysis() when the visuals are done
    ndva_quarters = [
        {"year": 2025, "quarter": "Q1", "management_sentiment": "Positive", "score": 0.85},
        {"year": 2024, "quarter": "Q4", "management_sentiment": "Neutral", "score": 0.5},
        {"year": 2024, "quarter": "Q3", "management_sentiment": "Neutral", "score": 0.4},
        {"year": 2024, "quarter": "Q2", "management_sentiment": "Negative", "score": 0.2},
    ]

    labels = [f"{q['year']} {q['quarter']}" for q in ndva_quarters]
    scores = [q['score'] for q in ndva_quarters]

    return render_template('index.html', quarters=ndva_quarters, labels=labels, scores=scores)

if __name__ == '__main__':
    app.run(debug=True)