import logging
import os
import sys

import yaml
from flask import Flask

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import src.chat as chat
import src.embed as embed
import src.completions as completions

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config["port"])
