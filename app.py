import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return {"message": "Backend is running successfully 🎉"}

@app.route("/price", methods=["GET"])
def get_price():
    state = request.args.get("state", "").strip().lower()
    commodity = request.args.get("commodity", "").strip().lower()

    if not state or not commodity:
        return jsonify({"error": "Please provide state and commodity"}), 400

    url = f"https://www.napanta.com/agri-commodity-prices/{state}/{commodity}/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    rows = soup.select("table tr")
    data = []
    for row in rows:
        cols = row.find_all("td")
        if cols:
            data.append([col.text.strip() for col in cols])

    if not data:
        return jsonify({"error": "No data found. Site structure may have changed."}), 404

    return jsonify({
        "state": state,
        "commodity": commodity,
        "prices": data
    })

if __name__ == "__main__":
    app.run(debug=True, port=5001)
