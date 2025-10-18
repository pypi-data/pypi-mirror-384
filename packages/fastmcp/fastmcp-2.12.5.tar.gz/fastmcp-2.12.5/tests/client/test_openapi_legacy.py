import json
from collections.abc import Generator

import pytest
from fastapi import FastAPI, Request

from fastmcp import Client, FastMCP
from fastmcp.client.transports import SSETransport, StreamableHttpTransport
from fastmcp.server.openapi import MCPType, RouteMap
from fastmcp.utilities.tests import run_server_in_process


def fastmcp_server_for_headers() -> FastMCP:
    app = FastAPI()

    @app.get("/headers")
    def get_headers(request: Request):
        return request.headers

    @app.get("/headers/{header_name}")
    def get_header_by_name(header_name: str, request: Request):
        return request.headers[header_name]

    @app.post("/headers")
    def post_headers(request: Request):
        return request.headers

    mcp = FastMCP.from_fastapi(
        app,
        httpx_client_kwargs={"headers": {"x-server-header": "test-abc"}},
        route_maps=[
            # GET requests with path parameters go to ResourceTemplate
            RouteMap(
                methods=["GET"],
                pattern=r".*\{.*\}.*",
                mcp_type=MCPType.RESOURCE_TEMPLATE,
            ),
            # GET requests without path parameters go to Resource
            RouteMap(methods=["GET"], pattern=r".*", mcp_type=MCPType.RESOURCE),
        ],
    )

    return mcp


def run_server(host: str, port: int, **kwargs) -> None:
    fastmcp_server_for_headers().run(host=host, port=port, **kwargs)


def run_proxy_server(host: str, port: int, shttp_url: str, **kwargs) -> None:
    app = FastMCP.as_proxy(StreamableHttpTransport(shttp_url))
    app.run(host=host, port=port, **kwargs)


@pytest.fixture
def shttp_server() -> Generator[str, None, None]:
    with run_server_in_process(run_server, transport="http") as url:
        yield f"{url}/mcp"


@pytest.fixture
def sse_server() -> Generator[str, None, None]:
    with run_server_in_process(run_server, transport="sse") as url:
        yield f"{url}/sse"


@pytest.fixture
def proxy_server(shttp_server: str) -> Generator[str, None, None]:
    with run_server_in_process(
        run_proxy_server,
        shttp_url=shttp_server,
        transport="http",
    ) as url:
        yield f"{url}/mcp"


async def test_fastapi_client_headers_streamable_http_resource(shttp_server: str):
    async with Client(transport=StreamableHttpTransport(shttp_server)) as client:
        result = await client.read_resource("resource://get_headers_headers_get")
        headers = json.loads(result[0].text)  # type: ignore[attr-defined]
        assert headers["x-server-header"] == "test-abc"


async def test_fastapi_client_headers_sse_resource(sse_server: str):
    async with Client(transport=SSETransport(sse_server)) as client:
        result = await client.read_resource("resource://get_headers_headers_get")
        headers = json.loads(result[0].text)  # type: ignore[attr-defined]
        assert headers["x-server-header"] == "test-abc"


async def test_fastapi_client_headers_streamable_http_tool(shttp_server: str):
    async with Client(transport=StreamableHttpTransport(shttp_server)) as client:
        result = await client.call_tool("post_headers_headers_post")
        headers: dict[str, str] = result.data
        assert headers["x-server-header"] == "test-abc"


async def test_fastapi_client_headers_sse_tool(sse_server: str):
    async with Client(transport=SSETransport(sse_server)) as client:
        result = await client.call_tool("post_headers_headers_post")
        headers: dict[str, str] = result.data
        assert headers["x-server-header"] == "test-abc"


async def test_client_headers_sse_resource(sse_server: str):
    async with Client(
        transport=SSETransport(sse_server, headers={"X-TEST": "test-123"})
    ) as client:
        result = await client.read_resource("resource://get_headers_headers_get")
        headers = json.loads(result[0].text)  # type: ignore[attr-defined]
        assert headers["x-test"] == "test-123"


async def test_client_headers_shttp_resource(shttp_server: str):
    async with Client(
        transport=StreamableHttpTransport(shttp_server, headers={"X-TEST": "test-123"})
    ) as client:
        result = await client.read_resource("resource://get_headers_headers_get")
        headers = json.loads(result[0].text)  # type: ignore[attr-defined]
        assert headers["x-test"] == "test-123"


async def test_client_headers_sse_resource_template(sse_server: str):
    async with Client(
        transport=SSETransport(sse_server, headers={"X-TEST": "test-123"})
    ) as client:
        result = await client.read_resource(
            "resource://get_header_by_name_headers/x-test"
        )
        header = json.loads(result[0].text)  # type: ignore[attr-defined]
        assert header == "test-123"


async def test_client_headers_shttp_resource_template(shttp_server: str):
    async with Client(
        transport=StreamableHttpTransport(shttp_server, headers={"X-TEST": "test-123"})
    ) as client:
        result = await client.read_resource(
            "resource://get_header_by_name_headers/x-test"
        )
        header = json.loads(result[0].text)  # type: ignore[attr-defined]
        assert header == "test-123"


async def test_client_headers_sse_tool(sse_server: str):
    async with Client(
        transport=SSETransport(sse_server, headers={"X-TEST": "test-123"})
    ) as client:
        result = await client.call_tool("post_headers_headers_post")
        headers: dict[str, str] = result.data
        assert headers["x-test"] == "test-123"


async def test_client_headers_shttp_tool(shttp_server: str):
    async with Client(
        transport=StreamableHttpTransport(shttp_server, headers={"X-TEST": "test-123"})
    ) as client:
        result = await client.call_tool("post_headers_headers_post")
        headers: dict[str, str] = result.data
        assert headers["x-test"] == "test-123"


async def test_client_overrides_server_headers(shttp_server: str):
    async with Client(
        transport=StreamableHttpTransport(
            shttp_server, headers={"x-server-header": "test-client"}
        )
    ) as client:
        result = await client.read_resource("resource://get_headers_headers_get")
        headers = json.loads(result[0].text)  # type: ignore[attr-defined]
        assert headers["x-server-header"] == "test-client"


async def test_client_with_excluded_header_is_ignored(sse_server: str):
    async with Client(
        transport=SSETransport(
            sse_server,
            headers={
                "x-server-header": "test-client",
                "host": "1.2.3.4",
                "not-host": "1.2.3.4",
            },
        )
    ) as client:
        result = await client.read_resource("resource://get_headers_headers_get")
        headers = json.loads(result[0].text)  # type: ignore[attr-defined]
        assert headers["not-host"] == "1.2.3.4"
        assert headers["host"] == "fastapi"


async def test_client_headers_proxy(proxy_server: str):
    """
    Test that client headers are passed through the proxy to the remove server.
    """
    async with Client(transport=StreamableHttpTransport(proxy_server)) as client:
        result = await client.read_resource("resource://get_headers_headers_get")
        headers = json.loads(result[0].text)  # type: ignore[attr-defined]
        assert headers["x-server-header"] == "test-abc"
