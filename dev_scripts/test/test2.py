import json
import os

import requests

MODEL = os.getenv("MODEL", "gpt4o")
# Import the request

# API endpoint to POST
url = "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"

# Data to be sent as a POST in JSON format
data = {
    "user": "cels",
    "model": MODEL,
    "messages": [
        {
            "role": "user",
            "content": "A detailed description of the biochemical function 5-(hydroxymethyl)furfural/furfural transporter is",
        },
    ],
    "stop": [],
    "temperature": 0.0,
    "max_tokens": 2056,
}

# Convert the dict to JSON
payload = json.dumps(data)

# Add a header stating that the content type is JSON
headers = {"Content-Type": "application/json"}

# Send POST request
response = requests.post(url, data=payload, headers=headers)

# Receive the response data
# print("Status Code:", response.status_code)
# print("JSON Response ", response.json())
