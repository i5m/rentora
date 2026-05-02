"""ASGI <-> Cloudflare Workers bridge.

Vendored from cloudflare/ai (demos/python-workers-mcp). This shim translates
between Python ASGI applications (FastMCP, Starlette, FastAPI) and the
Workers runtime fetch handler.
"""

from asyncio import Event, Future, Queue, create_task, ensure_future, sleep
from contextlib import contextmanager
from inspect import isawaitable

ASGI = {"spec_version": "2.0", "version": "3.0"}

background_tasks = set()


def run_in_background(coro):
    fut = ensure_future(coro)
    background_tasks.add(fut)
    fut.add_done_callback(background_tasks.discard)


@contextmanager
def acquire_js_buffer(pybuffer):
    from pyodide.ffi import create_proxy

    px = create_proxy(pybuffer)
    buf = px.getBuffer()
    px.destroy()
    try:
        yield buf.data
    finally:
        buf.release()


def request_to_scope(req, env, ws=False):
    from js import URL

    headers = [(k.lower().encode(), v.encode()) for k, v in req.headers.items()]
    url = URL.new(req.url)
    assert url.protocol[-1] == ":"
    scheme = url.protocol[:-1]
    path = url.pathname
    assert "?".startswith(url.search[0:1])
    query_string = url.search[1:].encode()
    ty = "websocket" if ws else "http"
    return {
        "asgi": ASGI,
        "headers": headers,
        "http_version": "1.1",
        "method": req.method,
        "scheme": scheme,
        "path": path,
        "query_string": query_string,
        "type": ty,
        "env": env,
    }


async def start_application(app):
    shutdown_future = Future()

    async def shutdown():
        shutdown_future.set_result(None)
        await sleep(0)

    it = iter([{"type": "lifespan.startup"}, Future()])

    async def receive():
        res = next(it)
        if isawaitable(res):
            await res
        return res

    ready = Future()

    async def send(got):
        if got["type"] == "lifespan.startup.complete":
            ready.set_result(None)
            return
        if got["type"] == "lifespan.shutdown.complete":
            return
        raise RuntimeError(f"Unexpected lifespan event {got['type']}")

    run_in_background(
        app(
            {
                "asgi": ASGI,
                "state": {},
                "type": "lifespan",
            },
            receive,
            send,
        )
    )
    await ready
    return shutdown


async def process_request(app, req, env, ctx):
    from js import Object, Response, TransformStream
    from pyodide.ffi import create_proxy

    status = None
    headers = None
    result = Future()
    is_sse = False
    finished_response = Event()

    receive_queue = Queue()
    if req.body:
        async for data in req.body:
            await receive_queue.put(
                {
                    "body": data.to_bytes(),
                    "more_body": True,
                    "type": "http.request",
                }
            )
    await receive_queue.put({"body": b"", "more_body": False, "type": "http.request"})

    async def receive():
        message = None
        if not receive_queue.empty():
            message = await receive_queue.get()
        else:
            await finished_response.wait()
            message = {"type": "http.disconnect"}
        return message

    transform_stream = TransformStream.new()
    readable = transform_stream.readable
    writable = transform_stream.writable
    writer = writable.getWriter()

    async def send(got):
        nonlocal status
        nonlocal headers
        nonlocal is_sse

        if got["type"] == "http.response.start":
            status = got["status"]
            headers = [(k.decode(), v.decode()) for k, v in got["headers"]]
            for k, v in headers:
                if k.lower() == "content-type" and v.lower().startswith("text/event-stream"):
                    is_sse = True
                    break
            if is_sse:
                resp = Response.new(readable, headers=Object.fromEntries(headers), status=status)
                result.set_result(resp)

        elif got["type"] == "http.response.body":
            body = got["body"]
            more_body = got.get("more_body", False)

            px = create_proxy(body)
            buf = px.getBuffer()
            px.destroy()

            if is_sse:
                await writer.write(buf.data)
                if not more_body:
                    await writer.close()
                    finished_response.set()
            else:
                resp = Response.new(buf.data, headers=Object.fromEntries(headers), status=status)
                result.set_result(resp)
                await writer.close()
                finished_response.set()

    async def run_app():
        try:
            await app(request_to_scope(req, env), receive, send)

            if not result.done():
                raise RuntimeError("The application did not generate a response")
        except Exception as e:
            if not result.done():
                result.set_exception(e)
            await writer.close()
            finished_response.set()

    app_task = create_task(run_app())

    response = await result

    if not is_sse:
        await app_task
    elif ctx is not None:
        ctx.waitUntil(create_proxy(app_task))
    else:
        raise RuntimeError("Server-Side-Events require ctx to be passed to asgi.fetch")
    return response


async def process_websocket(app, req):
    from js import Response, WebSocketPair

    client, server = WebSocketPair.new().object_values()
    server.accept()
    queue = Queue()

    def onopen(evt):
        msg = {"type": "websocket.connect"}
        queue.put_nowait(msg)

    onopen(1)

    def onclose(evt):
        msg = {"type": "websocket.close", "code": evt.code, "reason": evt.reason}
        queue.put_nowait(msg)

    def onmessage(evt):
        msg = {"type": "websocket.receive", "text": evt.data}
        queue.put_nowait(msg)

    server.onopen = onopen
    server.onopen = onclose
    server.onmessage = onmessage

    async def ws_send(got):
        if got["type"] == "websocket.send":
            b = got.get("bytes", None)
            s = got.get("text", None)
            if b:
                with acquire_js_buffer(b) as jsbytes:
                    server.send(jsbytes)
            if s:
                server.send(s)

        else:
            print(" == Not implemented", got["type"])

    async def ws_receive():
        received = await queue.get()
        return received

    env = {}
    run_in_background(app(request_to_scope(req, env, ws=True), ws_receive, ws_send))

    return Response.new(None, status=101, webSocket=client)


async def fetch(app, req, env, ctx=None):
    shutdown = await start_application(app)
    result = await process_request(app, req, env, ctx)
    await shutdown()
    return result


async def websocket(app, req):
    return await process_websocket(app, req)


def __getattr__(name):
    if name == "env":
        from fastapi import Depends, Request

        @Depends
        async def env(request: Request):
            return request.scope["env"]

        return env

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
