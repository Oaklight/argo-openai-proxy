import logging
import os
import sys

import yaml
from flask import Flask

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import argoproxy.chat as chat
import argoproxy.embed as embed
import argoproxy.completions as completions
import argoproxy.extras as extras  # Import the new extras module

app = Flask(__name__)

# Read configuration from YAML file
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)


@app.route("/v1/chat", methods=["POST"])
def proxy_argo_chat_directly():
    return chat.proxy_request(convert_to_openai=False)


@app.route("/v1/chat/completions", methods=["POST"])
def proxy_openai_chat_compatible():
    return chat.proxy_request(convert_to_openai=True)


@app.route("/v1/completions", methods=["POST"])
def proxy_openai_legacy_completions_compatible():
    return completions.proxy_request(convert_to_openai=True)


@app.route("/v1/embed", methods=["POST"])
def proxy_embedding_request():
    return embed.proxy_request(convert_to_openai=False)


# Add new endpoints for /models and /status
@app.route("/v1/models", methods=["GET"])
def get_models():
    return extras.get_models()


@app.route("/v1/status", methods=["GET"])
def get_status():
    return extras.get_status()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config["port"])
