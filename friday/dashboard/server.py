from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
import jinja2
import os

from friday.dashboard.memory_ops import list_all, search, edit, stats, export
from friday.tools.memory import forget, _get_collection

app = FastAPI(title="F.R.I.I.D.A.Y. Memory Dashboard")

# Simple template loader — no caching, always fresh from disk
_TEMPLATE_DIR = "friday/dashboard/templates"


def _render_template(name: str, context: dict) -> str:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(_TEMPLATE_DIR),
        autoescape=jinja2.select_autoescape(["html", "xml"]),
    )
    template = env.get_template(name)
    return template.render(**context)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    grouped = list_all()
    html = _render_template("index.html", {"request": request, "grouped": grouped})
    return HTMLResponse(content=html)


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, q: str = ""):
    results = search(q, limit=10) if q else []
    html = _render_template("search.html", {"request": request, "results": results, "query": q})
    return HTMLResponse(content=html)


@app.get("/memory/{memory_id}", response_class=HTMLResponse)
async def memory_detail(request: Request, memory_id: str):
    collection = _get_collection()
    result = collection.get(ids=[memory_id], include=["documents", "metadatas"])
    if not result["ids"]:
        return HTMLResponse("Memory not found", status_code=404)
    memory = {"memory_id": memory_id, "content": result["documents"][0], **result["metadatas"][0]}
    html = _render_template("memory_detail.html", {"request": request, "memory": memory})
    return HTMLResponse(content=html)


@app.post("/memory/{memory_id}/edit")
async def edit_memory(memory_id: str, content: str = Form(...)):
    return JSONResponse(edit(memory_id, content))


@app.post("/memory/{memory_id}/delete")
async def delete_memory(memory_id: str):
    return JSONResponse(forget(memory_id))


@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    html = _render_template("stats.html", {"request": request, "stats": stats()})
    return HTMLResponse(content=html)


@app.get("/export")
async def export_memories(category: str = None):
    return JSONResponse(export(category=category))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7272)
