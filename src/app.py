# from flask import Flask, render_template

# app = Flask(__name__)

# @app.route('/')
# def hello():
#     return render_template('index.html')

# if __name__ == '__main__':
#     app.run(debug=True)

from flask import Flask, render_template
from model import ndva_analysis

app = Flask(__name__)

@app.route('/')
def index():
    ndva_quarters = ndva_analysis(return_results=True)
    ndva_quarters = [
        {"year": 2025, "quarter": "Q1", "management_sentiment": "Positive", "score": 0.85},
        {"year": 2024, "quarter": "Q4", "management_sentiment": "Neutral", "score": 0.5},
        # ... more quarters
    ]
    return render_template('index.html', quarters=ndva_quarters)

if __name__ == '__main__':
    app.run(debug=True)