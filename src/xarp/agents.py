import asyncio
import inspect
import threading
from sys import argv
from typing import Any, Callable

import uvicorn
from fastapi import FastAPI
from fastmcp import FastMCP
from smolagents import tool, CodeAgent, MultiStepAgent, ActionStep
from smolagents.tools import Tool
from starlette.websockets import WebSocket

from xarp import server
from xarp.entities import ImageAsset
from xarp.express import SyncXR, AsyncXR, SyncSimpleXR, AsyncSimpleXR
from xarp.remote import RemoteXRClient
from xarp.server import show_qrcode_link
from xarp.settings import settings

XRAgentApp = Callable[[SyncXR, MultiStepAgent, dict[str, Any]], None]

_DEFAULT_ALLOWED_TOOLS = (
    "info",
    "write",
    "baseline_code",
    "say",
    "read",
    "passthrough",
    "image",
    "virtual_image",
    "depth",
    "eye",
    "head",
    "hands",
    "list_assets",
    "list_elements",
    "destroy_element",
    "create_or_update_glb",
    "create_or_update_label",
    "create_or_update_cube",
    "create_or_update_sphere",
    "create_or_update_image"
)


class ImageAssetToolInterceptor:

    def __init__(self):
        self.intercepted_images = []

    def intercept(self, image_asset_tool: Tool):
        tool_forward = image_asset_tool.forward

        def _wrapper(*args, **kwargs):
            image_asset: ImageAsset = tool_forward(*args, **kwargs)
            self.intercepted_images.append(image_asset.obj)
            n_images = len(self.intercepted_images)
            print("Images to observe:", n_images)

        image_asset_tool.forward = _wrapper

    def provide_observations(self, step: ActionStep):
        step.observations_images = [img.copy() for img in self.intercepted_images]

    @staticmethod
    def attach_to_agent(agent: MultiStepAgent):
        interceptor = ImageAssetToolInterceptor()
        for _tool in agent.tools.values():
            if _tool.forward.__annotations__["return"] is ImageAsset:
                interceptor.intercept(_tool)
        agent.step_callbacks.register(ActionStep, interceptor.provide_observations)


def _get_public_methods(obj, allowed_tools: tuple[str, ...] | None = None) -> list[tuple[str, Any]]:
    if allowed_tools is None:
        allowed_tools = _DEFAULT_ALLOWED_TOOLS
    
    public_methods = []
    for pair in inspect.getmembers(obj, inspect.ismethod):
        name = pair[0]
        if not name.startswith("_") and name in allowed_tools:
            public_methods.append(pair)
    return public_methods


def as_agent_tools(xr: SyncXR, allowed_tools: tuple[str, ...] | None = None) -> list[Tool]:
    tools = [tool(member) for name, member in _get_public_methods(xr, allowed_tools)]
    return tools


def run_xr_agent(xr_agent_app: XRAgentApp, model, allowed_tools: tuple[str, ...] | list[str] | None = None, **kwargs) -> None:
    async def _with_agent(axr: AsyncXR, params: dict[str, Any]) -> None:
        loop = asyncio.get_running_loop()
        tools_filter = tuple(allowed_tools) if allowed_tools is not None else None
        agent = CodeAgent(
            tools=as_agent_tools(sxr, tools_filtete, loop, loop_thread)

        agent = CodeAgent(
            tools=as_agent_tools(sxr),
            model=model,
            **kwargs
        )

        ImageAssetToolInterceptor.attach_to_agent(agent)

        await asyncio.to_thread(xr_agent_app, sxr, agent, params)

    server.run(_with_agent)


def run_mcp():
    async def entrypoint(ws: WebSocket) -> None:
        await ws.accept()

        remote = RemoteXRClient(ws)
        await remote.start()
        asxr = AsyncSimpleXR(remote)

        mcp = FastMCP(
            argv[1],
            host="127.0.0.1",
            port=argv[2]
        )

        for name, method in _get_public_methods(asxr):
            mcp.tool(method)

        try:
            await mcp.run_http_async(show_banner=False)
        finally:
            remote.stop()

    app = FastAPI()
    app.add_api_websocket_route(
        settings.ws_path,
        entrypoint)

    show_qrcode_link()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        ws_max_size=100 * 1024 ** 2  # 100MB
    )


if __name__ == '__main__':
    run_mcp()
