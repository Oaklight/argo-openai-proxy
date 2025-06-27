import os

from aiohttp import web
from loguru import logger

from .__init__ import __version__
from .config import load_config
from .endpoints import chat, completions, embed, extras, responses
from .endpoints.extras import get_latest_pypi_version
from .models import ModelRegistry


async def prepare_app(app):
    """Load configuration without validation for worker processes"""
    config_path = os.getenv("CONFIG_PATH")
    app["config"], _ = load_config(config_path, verbose=False)
    app["model_registry"] = ModelRegistry(config=app["config"])
    await app["model_registry"].initialize()


# ================= Argo Direct Access =================


async def proxy_argo_chat_directly(request: web.Request):
    logger.info("/v1/chat")
    return await chat.proxy_request(request, convert_to_openai=False)


async def proxy_embedding_directly(request: web.Request):
    logger.info("/v1/embed")
    return await embed.proxy_request(request, convert_to_openai=False)


# ================= OpenAI Compatible =================


async def proxy_openai_chat_compatible(request: web.Request):
    logger.info("/v1/chat/completions")
    return await chat.proxy_request(request)


async def proxy_openai_legacy_completions_compatible(request: web.Request):
    logger.info("/v1/completions")
    return await completions.proxy_request(request)


async def proxy_openai_responses_request(request: web.Request):
    logger.info("/v1/responses")
    return await responses.proxy_request(request)


async def proxy_openai_embedding_request(request: web.Request):
    logger.info("/v1/embeddings")
    return await embed.proxy_request(request, convert_to_openai=True)


async def get_models(request: web.Request):
    logger.info("/v1/models")
    return extras.get_models(request)


async def docs(request: web.Request):
    msg = "<html><body>Documentation access: Please visit <a href='https://oaklight.github.io/argo-openai-proxy'>https://oaklight.github.io/argo-openai-proxy</a> for full documentation.</body></html>"
    return web.Response(text=msg, status=200, content_type="text/html")


async def health_check(request: web.Request):
    logger.info("/health")
    return web.json_response({"status": "healthy"}, status=200)


async def get_version(request: web.Request):
    logger.info("/version")
    latest = await get_latest_pypi_version()
    update_available = latest and latest != __version__

    response = {
        "version": __version__,
        "latest": latest,
        "up_to_date": not update_available,
        "pypi": "https://pypi.org/project/argo-proxy/",
    }

    if update_available:
        response.update(
            {
                "message": f"New version {latest} available",
                "install_command": "pip install --upgrade argo-proxy",
            }
        )
    else:
        response["message"] = "You're using the latest version"

    return web.json_response(response)


app = web.Application()
app.on_startup.append(prepare_app)

# openai incompatible
app.router.add_post("/v1/chat", proxy_argo_chat_directly)
app.router.add_post("/v1/embed", proxy_embedding_directly)

# openai compatible
app.router.add_post("/v1/chat/completions", proxy_openai_chat_compatible)
app.router.add_post("/v1/completions", proxy_openai_legacy_completions_compatible)
app.router.add_post("/v1/responses", proxy_openai_responses_request)
app.router.add_post("/v1/embeddings", proxy_openai_embedding_request)
app.router.add_get("/v1/models", get_models)

# extras
app.router.add_get("/v1/docs", docs)
app.router.add_get("/health", health_check)
app.router.add_get("/version", get_version)


def run(*, host: str = "0.0.0.0", port: int = 8080):
    web.run_app(app, host=host, port=port)
