import logging
import os
import sys

from sanic import Sanic, response

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import argoproxy.chat as chat
import argoproxy.completions as completions
import argoproxy.embed as embed
import argoproxy.extras as extras
from argoproxy.config import config

app = Sanic("ArgoProxy")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@app.route("/v1/chat", methods=["POST"])
async def proxy_argo_chat_directly(request):
    return await chat.proxy_request(convert_to_openai=False, request=request)


@app.route("/v1/chat/completions", methods=["POST"])
async def proxy_openai_chat_compatible(request):
    return await chat.proxy_request(convert_to_openai=True, request=request)


@app.route("/v1/completions", methods=["POST"])
async def proxy_openai_legacy_completions_compatible(request):
    return await completions.proxy_request(convert_to_openai=True, request=request)


@app.route("/v1/embeddings", methods=["POST"])
async def proxy_embedding_request(request):
    return await embed.proxy_request(request)


@app.route("/v1/models", methods=["GET"])
async def get_models(request):
    return extras.get_models()


@app.route("/v1/status", methods=["GET"])
async def get_status(request):
    return await extras.get_status()


@app.route("/health", methods=["GET"])
async def health_check(request):
    return response.json({"status": "healthy"}, status=200)


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=config["port"])
    except KeyError:
        logger.error("Port not specified in configuration file.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred while starting the server: {e}")
        sys.exit(1)
