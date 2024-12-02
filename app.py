from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Replace this with OpenAI-compatible API URL
ARGO_API_URL = "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"


@app.route("/v1/chat/completions", methods=["POST"])
@app.route("/v1/chat", methods=["POST"])
def proxy_request():
    # Retrieve the incoming JSON data
    data = request.get_json()  # convert to utf8
    if not data:
        return jsonify({"error": "Invalid input. Expected JSON data."}), 400
    # print(data)

    # Automatically replace or insert the user
    data["user"] = "cels"

    headers = {
        "Content-Type": "application/json"
        # Uncomment and customize if needed
        # "Authorization": f"Bearer {YOUR_API_KEY}"
    }

    # Forward the modified request to the actual API
    response = requests.post(ARGO_API_URL, headers=headers, json=data)

    # print(response.json())

    # Return the response from the external API to the local client
    return jsonify(response.json())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000)
