import os

from aiohttp import web
from loguru import logger

from . import chat, completions, embed, extras
from .config import load_config


async def setup_config(app):
    """Load configuration without validation for worker processes"""
    config_path = os.getenv("CONFIG_PATH")
    app["config"], _ = load_config(config_path)


async def proxy_argo_chat_directly(request: web.Request):
    logger.info("/v1/chat")

    return await chat.proxy_request(request, convert_to_openai=False)


async def proxy_openai_chat_compatible(request: web.Request):
    logger.info("/v1/chat/completions")

    return await chat.proxy_request(request, convert_to_openai=True)


async def proxy_openai_legacy_completions_compatible(request: web.Request):
    logger.info("/v1/completions")

    return await completions.proxy_request(request, convert_to_openai=True)


async def proxy_embedding_request(request: web.Request):
    logger.info("/v1/embeddings")
    return await embed.proxy_request(request, convert_to_openai=True)


async def get_models(request: web.Request):
    logger.info("/v1/models")
    return extras.get_models()


async def get_status(request: web.Request):
    logger.info("/v1/status")
    return await extras.get_status()


async def docs(request: web.Request):
    msg = "Documentation access: Please visit https://oaklight.github.io/argo-proxy for full documentation.\n"
    return web.Response(text=msg, status=200)


async def health_check(request: web.Request):
    logger.info("/health")
    return web.json_response({"status": "healthy"}, status=200)


app = web.Application()
app.on_startup.append(setup_config)

app.router.add_post("/v1/chat", proxy_argo_chat_directly)
app.router.add_post("/v1/chat/completions", proxy_openai_chat_compatible)
app.router.add_post("/v1/completions", proxy_openai_legacy_completions_compatible)
app.router.add_post("/v1/embeddings", proxy_embedding_request)
app.router.add_get("/v1/models", get_models)
app.router.add_get("/v1/status", get_status)

app.router.add_get("/v1/docs", docs)

app.router.add_get("/health", health_check)


def run(*, host: str = "0.0.0.0", port: int = 8080):
    web.run_app(app, host=host, port=port)
