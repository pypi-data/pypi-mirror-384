import json
import asyncio
import threading
from typing import Any, Dict, Callable, Optional, TypedDict
from asyncio import Future

from ..lib.browser import BrowserSetup, get_agent_ws_url


class AgentTaskParams(TypedDict, total=False):
    url: Optional[str]
    output_schema: Optional[Dict[str, Any]]
    on_agent_step: Optional[Callable[[str], None]]


def create_task_payload(prompt: str, output_schema: Optional[Dict[str, Any]] = None) -> str:
    if not prompt or prompt.strip() == "":
        raise ValueError("Prompt cannot be empty")

    return json.dumps(
        {
            "prompt": prompt,
            "output_schema": output_schema,
        }
    )


def on_agent_step_sync(on_agent_step: Callable[[str], None], browser_setup: BrowserSetup) -> Future[None]:
    import websockets

    async def websocket_listener() -> None:
        ws_url = get_agent_ws_url(browser_setup.base_url, browser_setup.session_id)
        try:
            async with websockets.connect(ws_url) as ws:
                async for ws_msg in ws:
                    on_agent_step(str(ws_msg))
        except Exception as e:
            future.set_exception(e)

    def run_in_thread() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(websocket_listener())
        finally:
            loop.close()

    # Create a future to track the task
    future = Future[None]()
    try:
        thread = threading.Thread(target=lambda: future.set_result(run_in_thread()))
        thread.daemon = True
        thread.start()
    except Exception:
        pass

    return future


def on_agent_step_async(on_agent_step: Callable[[str], None], browser_setup: BrowserSetup) -> None:
    import websockets

    async def websocket_listener() -> None:
        ws_url = get_agent_ws_url(browser_setup.base_url, browser_setup.session_id)
        async with websockets.connect(ws_url) as ws:
            async for ws_msg in ws:
                on_agent_step(str(ws_msg))

    asyncio.create_task(websocket_listener())
