import json

import requests

# API endpoint to POST
# url = "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/embed/"

url = "http://localhost:5000/v1/embeddings"
MODEL = "argo:text-embedding-3-large"

# Data to be sent as a POST in JSON format

data = {
    "model": MODEL,
    "input": ["What is your name", "What is your favorite color?"],
}

# Convert the dict to JSON

payload = json.dumps(data)

# Adding a header stating that the content type is JSON

headers = {"Content-Type": "application/json"}

# Send POST request

response = requests.post(url, data=payload, headers=headers)

# Receive the response data

print("Status Code:", response.status_code)
print("JSON Response ", response.json())
