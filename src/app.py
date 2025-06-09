from flask import Flask, render_template
from model import ndva_analysis

app = Flask(__name__)

@app.route('/')
def index():
    # Switch to ndva_analysis() when the visuals are done
    ndva_quarters = ndva_analysis() 

    # Prepare data
    labels = [f"{r['year']} {r['quarter']}" for r in ndva_quarters]
    management_scores = [r["management_sentiment"]["score"] for r in ndva_quarters]
    qna_scores = [r["qna_sentiment"]["score"] for r in ndva_quarters]
    
    return render_template('index.html', quarters=ndva_quarters, labels=labels, 
                           management_scores=management_scores, qna_scores=qna_scores)


if __name__ == '__main__':
    app.run(debug=True)
    
    
    