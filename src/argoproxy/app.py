import os

from sanic import Sanic, response
from sanic.log import logger

from . import chat, completions, embed, extras
from .config import load_config

app = Sanic("ArgoProxy")


@app.before_server_start
async def setup_config(app, loop):
    """Load configuration without validation for worker processes"""
    config_path = os.getenv("CONFIG_PATH")
    app.ctx.config, _ = load_config(config_path)


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
