from flask import Flask

app = Flask(__name__)  # Create app instance

@app.route("/")  # URL route
def home():
    return "Hello, Flask!"  # What to show on homepage

if __name__ == "__main__":
    app.run(debug=True)  # Start development server