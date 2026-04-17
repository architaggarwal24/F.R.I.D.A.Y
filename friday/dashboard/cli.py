import click
import json
import os
from friday.dashboard.memory_ops import (
    list_all, delete_one, bulk_delete,
    export as export_op, stats as stats_op,
    search as search_op, edit as edit_op,
)


@click.group()
def memory():
    """F.R.I.D.A.Y. memory management CLI."""
    pass


@memory.command()
def list():
    grouped = list_all()
    for category, memories in grouped.items():
        click.echo(f"\n-- {category.upper()} ({len(memories)}) --")
        for m in memories:
            click.echo(f"  [{m['memory_id'][:8]}] {m['content'][:80]}")


@memory.command()
@click.argument("query")
@click.option("--limit", default=10)
def search(query, limit):
    results = search_op(query, limit=limit)
    if not results:
        click.echo("No results found.")
        return
    for r in results:
        click.echo(f"  [{r['relevance_score']:.2f}] {r['content'][:80]}")


@memory.command()
@click.argument("memory_id", required=False)
@click.option("--category", default=None)
def delete(memory_id, category):
    if category:
        result = bulk_delete(category)
        click.echo(f"Deleted {result['deleted']} memories in category '{category}'")
    elif memory_id:
        result = delete_one(memory_id)
        click.echo(result["status"])
    else:
        click.echo("Provide a memory_id or --category flag.")


@memory.command()
@click.argument("memory_id")
def edit(memory_id):
    new_content = click.prompt("New content")
    result = edit_op(memory_id, new_content)
    click.echo(result["status"])


@memory.command()
@click.option("--category", default=None)
def export_cmd(category):
    os.makedirs("friday/exports", exist_ok=True)
    memories = export_op(category=category)
    path = "friday/exports/memories.json"
    with open(path, "w") as f:
        json.dump(memories, f, indent=2)
    click.echo(f"Exported {len(memories)} memories to {path}")


@memory.command()
@click.option("--port", default=7272)
@click.option("--host", default="127.0.0.1")
def serve(port, host):
    """Launch the F.R.I.D.A.Y. memory dashboard web UI."""
    import uvicorn
    click.echo(f"Launching F.R.I.D.A.Y. Memory Dashboard at http://{host}:{port}")
    uvicorn.run("friday.dashboard.server:app", host=host, port=port, reload=True)


@memory.command()
def stats():
    result = stats_op()
    click.echo(f"Total memories: {result['total']}")
    click.echo(f"Store size: {result['store_size_bytes']:,} bytes")
    for cat, count in result["by_category"].items():
        click.echo(f"  {cat}: {count}")


if __name__ == "__main__":
    memory()
