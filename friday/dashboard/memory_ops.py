import os
from friday.tools.memory import remember, recall, forget, _get_collection, CHROMA_PERSIST_PATH


def list_all(grouped=True) -> dict:
    collection = _get_collection()
    results = collection.get(include=["documents", "metadatas"])
    memories = [
        {"memory_id": id_, "content": doc, **meta}
        for id_, doc, meta in zip(
            results["ids"], results["documents"], results["metadatas"]
        )
    ]
    if not grouped:
        return {"memories": memories}
    grouped_result = {}
    for m in memories:
        cat = m.get("category", "uncategorized")
        grouped_result.setdefault(cat, []).append(m)
    return grouped_result


def search(query: str, limit: int = 10) -> list[dict]:
    return recall(query, limit=limit)


def edit(memory_id: str, new_content: str) -> dict:
    collection = _get_collection()
    existing = collection.get(ids=[memory_id], include=["metadatas"])
    if not existing["ids"]:
        return {"status": "not_found"}
    original_category = existing["metadatas"][0].get("category", "fact")
    forget(memory_id)
    result = remember(new_content, category=original_category)
    return {"status": "updated", "new_memory_id": result["memory_id"]}


def bulk_delete(category: str) -> dict:
    collection = _get_collection()
    results = collection.get(include=["metadatas"], where={"category": category})
    if not results["ids"]:
        return {"deleted": 0}
    collection.delete(ids=results["ids"])
    return {"deleted": len(results["ids"])}


def delete_one(memory_id: str) -> dict:
    return forget(memory_id)


def export(category: str = None) -> list[dict]:
    collection = _get_collection()
    kwargs = {"include": ["documents", "metadatas"]}
    if category:
        kwargs["where"] = {"category": category}
    results = collection.get(**kwargs)
    return [
        {"memory_id": id_, "content": doc, **meta}
        for id_, doc, meta in zip(
            results["ids"], results["documents"], results["metadatas"]
        )
    ]


def stats() -> dict:
    grouped = list_all(grouped=True)
    total = sum(len(v) for v in grouped.values())
    by_category = {cat: len(mems) for cat, mems in grouped.items()}
    store_size = sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, _, files in os.walk(CHROMA_PERSIST_PATH)
        for f in files
    ) if os.path.exists(CHROMA_PERSIST_PATH) else 0
    return {"total": total, "by_category": by_category, "store_size_bytes": store_size}
