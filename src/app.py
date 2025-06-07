from flask import Flask, render_template
from model import ndva_analysis

app = Flask(__name__)

@app.route('/')
def index():
    # Switch to ndva_analysis() when the visuals are done
    ndva_quarters = [
    {
        "year": "2025",
        "quarter": "Q1",
        "management_sentiment": {"label": "POSITIVE", "score": 0.87},
        "qna_sentiment": {"label": "NEUTRAL", "score": 0.45},
        "themes": ["AI growth", "data center expansion", "gaming market"],
        "transcript": [
                {
                    "speaker": "Jensen Huang",
                    "title": "CEO",
                    "content": "We're seeing unprecedented demand for generative AI across industries, and our GPUs remain the cornerstone of accelerated computing."
                },
                {
                    "speaker": "Colette Kress",
                    "title": "CFO",
                    "content": "Revenue in our data center segment more than doubled, reflecting strong enterprise adoption and AI training workloads."
                }
            ]
        },
    {
        "year": "2024",
        "quarter": "Q4",
        "management_sentiment": {"label": "NEUTRAL", "score": 0.52},
        "qna_sentiment": {"label": "NEGATIVE", "score": 0.28},
        "themes": ["supply chain", "AI integration", "automotive AI"],
        "transcript": ["AAAA", "BBBB", "CCCCC"],"transcript": [
                {
                    "speaker": "Jensen Huang",
                    "title": "CEO",
                    "content": "We're seeing unprecedented demand for generative AI across industries, and our GPUs remain the cornerstone of accelerated computing."
                },
                {
                    "speaker": "Colette Kress",
                    "title": "CFO",
                    "content": "Revenue in our data center segment more than doubled, reflecting strong enterprise adoption and AI training workloads."
                }
            ]
        },
    {
        "year": "2024",
        "quarter": "Q3",
        "management_sentiment": {"label": "NEGATIVE", "score": 0.30},
        "qna_sentiment": {"label": "NEGATIVE", "score": 0.20},
        "themes": ["China regulations", "inventory", "operational costs"],
        "transcript": [
                {
                    "speaker": "Jensen Huang",
                    "title": "CEO",
                    "content": "We're seeing unprecedented demand for generative AI across industries, and our GPUs remain the cornerstone of accelerated computing."
                },
                {
                    "speaker": "Colette Kress",
                    "title": "CFO",
                    "content": "Revenue in our data center segment more than doubled, reflecting strong enterprise adoption and AI training workloads."
                }
            ]
        },
    {
        "year": "2024",
        "quarter": "Q2",
        "management_sentiment": {"label": "POSITIVE", "score": 0.76},
        "qna_sentiment": {"label": "POSITIVE", "score": 0.67},
        "themes": ["Hopper GPUs", "enterprise demand", "cloud partnerships"],
        "transcript": [
                {
                    "speaker": "Jensen Huang",
                    "title": "CEO",
                    "content": "We're seeing unprecedented demand for generative AI across industries, and our GPUs remain the cornerstone of accelerated computing."
                },
                {
                    "speaker": "Colette Kress",
                    "title": "CFO",
                    "content": "Revenue in our data center segment more than doubled, reflecting strong enterprise adoption and AI training workloads."
                }
            ]
    },
]

    # Prepare data
    labels = [f"{r['year']} {r['quarter']}" for r in ndva_quarters]
    management_scores = [r["management_sentiment"]["score"] for r in ndva_quarters]
    qna_scores = [r["qna_sentiment"]["score"] for r in ndva_quarters]
    
    return render_template('index.html', quarters=ndva_quarters, labels=labels, 
                           management_scores=management_scores, qna_scores=qna_scores)


if __name__ == '__main__':
    app.run(debug=True)
    
    
    