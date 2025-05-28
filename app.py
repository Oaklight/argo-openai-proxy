from sanic import Sanic, response
from sanic.log import logger

import argoproxy.chat as chat
import argoproxy.completions as completions
import argoproxy.embed as embed
import argoproxy.extras as extras
from argoproxy.config import config

app = Sanic("ArgoProxy")

# Configure Sanic's logger to use our settings
logger.setLevel(config["logging_level"])


@app.route("/v1/chat", methods=["POST"])
async def proxy_argo_chat_directly(request):
    logger.info("/v1/chat")
    stream = request.json.get("stream", False)
    timeout = request.json.get("timeout", None)
    logger.debug(request.json)
    return await chat.proxy_request(
        convert_to_openai=False, request=request, stream=stream, timeout=timeout
    )


@app.route("/v1/chat/completions", methods=["POST"])
async def proxy_openai_chat_compatible(request):
    logger.info("/v1/chat/completions")
    stream = request.json.get("stream", False)
    timeout = request.json.get("timeout", None)
    logger.debug(request.json)
    return await chat.proxy_request(
        convert_to_openai=True, request=request, stream=stream, timeout=timeout
    )


@app.route("/v1/completions", methods=["POST"])
async def proxy_openai_legacy_completions_compatible(request):
    logger.info("/v1/completions")
    logger.debug(request.json)
    stream = request.json.get("stream", False)
    timeout = request.json.get("timeout", None)
    return await completions.proxy_request(
        convert_to_openai=True, request=request, stream=stream, timeout=timeout
    )


@app.route("/v1/embeddings", methods=["POST"])
async def proxy_embedding_request(request):
    logger.info("/v1/embeddings")
    logger.debug(request.json)
    return await embed.proxy_request(request, convert_to_openai=True)


@app.route("/v1/models", methods=["GET"])
async def get_models(request):
    logger.info("/v1/models")
    return extras.get_models()


@app.route("/v1/status", methods=["GET"])
async def get_status(request):
    logger.info("/v1/status")
    return await extras.get_status()


@app.route("/v1/docs", methods=["GET"])
async def docs(request):
    msg = "Documentation access: Please visit https://oaklight.github.io/argo-proxy for full documentation.\n"
    return response.text(msg, status=200)


@app.route("/health", methods=["GET"])
async def health_check(request):
    logger.info("/health")
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
