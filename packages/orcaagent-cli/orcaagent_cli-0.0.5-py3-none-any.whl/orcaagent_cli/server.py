# server.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import StreamingResponse, Response
import httpx, os

GRAPH = os.getenv("GRAPH_URL", "http://localhost:8123")
UI_DIR = "agent-chat-ui/out"  # next export 产物；若用 SSR，改用 next start 方案

app = FastAPI()
app.mount("/", StaticFiles(directory=UI_DIR, html=True), name="ui")

# 普通 REST 反代
@app.api_route("/api/{path:path}", methods=["GET","POST","PUT","PATCH","DELETE"])
async def proxy_api(request: Request, path: str):
    async with httpx.AsyncClient(timeout=None) as client:
        upstream = f"{GRAPH}/api/{path}"
        resp = await client.request(
            request.method, upstream,
            params=dict(request.query_params),
            content=await request.body(),
            headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
        )
        return Response(content=resp.content, status_code=resp.status_code, headers=resp.headers)

# SSE 流式转发（/stream）
@app.get("/stream")
async def proxy_stream(request: Request):
    async with httpx.AsyncClient(timeout=None) as client:
        upstream = f"{GRAPH}/stream"
        r = await client.stream("GET", upstream, headers={"accept": "text/event-stream"})
        async def gen():
            async for chunk in r.aiter_raw():
                yield chunk
        return StreamingResponse(gen(), media_type="text/event-stream")
