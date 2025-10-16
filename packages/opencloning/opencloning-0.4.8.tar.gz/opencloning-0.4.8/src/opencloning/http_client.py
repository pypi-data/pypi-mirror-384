# Response is imported into other modules from here
from httpx import (  # noqa: F401
    Response,
    AsyncClient,
    ConnectError,
    TimeoutException,
    AsyncHTTPTransport,
    Request,
)
from urllib.error import HTTPError
import ssl
import certifi
from .app_settings import settings

allowed_external_urls = settings.ALLOWED_EXTERNAL_URLS

if settings.PLANNOTATE_URL:
    allowed_external_urls.append(settings.PLANNOTATE_URL)


class AllowedExternalUrlsTransport(AsyncHTTPTransport):
    async def handle_async_request(self, request: Request) -> Response:
        if any(str(request.url).startswith(url) for url in allowed_external_urls):
            return await super().handle_async_request(request)
        raise HTTPError(request.url, 403, f'Request to {request.url} is not allowed', None, None)


proxy = None
if settings.PROXY_URL:
    proxy = settings.PROXY_URL


def get_http_client():
    transport = AllowedExternalUrlsTransport()
    client_ctx = None
    if proxy is not None:
        client_ctx = ssl.create_default_context(cafile=certifi.where())
        if settings.PROXY_CERT_FILE:
            client_ctx.load_verify_locations(cafile=settings.PROXY_CERT_FILE)
    return AsyncClient(proxy=proxy, verify=client_ctx, transport=transport)
