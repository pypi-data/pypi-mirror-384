# retrieval.py
from collections import defaultdict
from itertools import chain
from typing import Any


def generate_cheatsheets(
    relevant_chunksets: list[dict[str, Any]], all_chunks: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    chunk_ids = [cs["chunks"] for cs in relevant_chunksets if "chunks" in cs]
    chunk_ids = list(chain.from_iterable(chunk_ids))  # flatten the list
    relevant_chunks = _get_relevant_chunks_for_ids(chunk_ids, all_chunks)
    sorted_chunks = sorted(
        relevant_chunks, key=lambda chunk: (chunk["tag"], chunk["chunk_index"])
    )
    return _cheatsheets_from_chunks(sorted_chunks)


def generate_single_cheatsheet(
    relevant_chunksets: list[dict[str, Any]], all_chunks: list[dict[str, Any]]
) -> str:

    def prepare_single_doc_chunks(
        chunk_dicts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        # Make sure there are no duplicate chunk_index values
        check_dict = defaultdict(set)
        has_duplicates = any(
            chunk["chunk_index"] in check_dict[chunk["tag"]]
            or check_dict[chunk["tag"]].add(chunk["chunk_index"])
            for chunk in chunk_dicts
        )
        if has_duplicates:
            raise ValueError(
                "Duplicate chunk indices found in single document mode. "
                "Each chunk must have a unique index."
            )
        # Use a fixed tag for chunks from single documents
        for chunk_dict in chunk_dicts:
            chunk_dict["tag"] = "single_doc"
        return chunk_dicts

    chunk_ids = [cs["chunks"] for cs in relevant_chunksets if "chunks" in cs]
    chunk_ids = list(chain.from_iterable(chunk_ids))  # flatten the list
    relevant_chunks = _get_relevant_chunks_for_ids(chunk_ids, all_chunks)
    relevant_chunks = prepare_single_doc_chunks(relevant_chunks)
    sorted_chunks = sorted(
        relevant_chunks, key=lambda chunk: (chunk["tag"], chunk["chunk_index"])
    )
    cheatsheets = _cheatsheets_from_chunks(sorted_chunks)
    if (
        not cheatsheets
        or not isinstance(cheatsheets, list)
        or len(cheatsheets) == 0
        or "content" not in cheatsheets[0]
    ):
        raise Exception(
            "Unknown error; cheatsheet could not be created from input chunks."
        )
    return cheatsheets[0]["content"]


def _get_relevant_chunks_for_ids(
    chunk_ids: list[int],
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    chunk_indices_of_retrieved_chunksets = chunk_ids
    all_chunks_of_doc = chunks

    # Build helpers
    sorted_chunks = sorted(all_chunks_of_doc, key=lambda c: c["chunk_index"])
    index_to_chunk = {c["chunk_index"]: c for c in sorted_chunks}
    index_to_depth = {c["chunk_index"]: c["depth"] for c in sorted_chunks}

    # Find relatively deepest indices in the retrieval
    candidate_indices = set(chunk_indices_of_retrieved_chunksets)

    def is_ancestor(idx1, idx2):
        """True if idx1 is an ancestor of idx2."""
        # idx1 must be before idx2 and have smaller depth
        if idx1 >= idx2:
            return False
        depth1 = index_to_depth[idx1]
        depth2 = index_to_depth[idx2]
        if depth1 >= depth2:
            return False
        # scan from idx1+1 up to idx2, making sure all are deeper than depth1 until idx2
        for i in range(idx1 + 1, idx2 + 1):
            depth = index_to_depth[sorted_chunks[i]["chunk_index"]]
            if depth <= depth1 and sorted_chunks[i]["chunk_index"] != idx2:
                return False
        return True

    # Exclude any index that is an ancestor of another in the set
    relatively_deepest = set(candidate_indices)
    for idx1 in candidate_indices:
        for idx2 in candidate_indices:
            if idx1 != idx2 and is_ancestor(idx1, idx2):
                relatively_deepest.discard(idx1)
                break

    # Standard subtree/parent finding routines
    def get_child_indices(chunk_index: int) -> list[int]:
        base_depth = index_to_depth[chunk_index]
        children = []
        for i in range(chunk_index + 1, len(sorted_chunks)):
            idx = sorted_chunks[i]["chunk_index"]
            depth = sorted_chunks[i]["depth"]
            if depth <= base_depth:
                break
            children.append(idx)
        return children

    def get_parent_indices(chunk_index: int) -> list[int]:
        parents = []
        current_depth = index_to_depth[chunk_index]
        for i in range(chunk_index - 1, -1, -1):
            idx = sorted_chunks[i]["chunk_index"]
            depth = sorted_chunks[i]["depth"]
            if depth < current_depth:
                parents.append(idx)
                current_depth = depth
        return parents[::-1]  # root -> leaf order

    # Collect all relevant indices
    all_indices = set(
        chunk_indices_of_retrieved_chunksets
    )  # always include all search hits
    for idx in relatively_deepest:
        all_indices.update(get_child_indices(idx))

    # Parents for all found nodes
    for idx in list(all_indices):
        all_indices.update(get_parent_indices(idx))

    # Return in doc order
    return [index_to_chunk[i] for i in sorted(all_indices)]


def _cheatsheets_from_chunks(
    content_chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    cheatsheets: list[dict] = []

    compressed_data = {}
    for chunk in content_chunks:
        if chunk["tag"] not in compressed_data:
            # If there is data stored for a previous tag, save it to the cheatsheets list
            if compressed_data:
                for key, value in compressed_data.items():
                    cheatsheets.append({"tag": key, "content": value["content"]})
            # Clear the compressed_data for the current tag
            compressed_data.clear()
            # Start a new entry for the current tag
            compressed_data[chunk["tag"]] = {
                "content": chunk["content"],
                "last_chunk": chunk["chunk_index"],
            }
        else:
            # Check if chunks are consecutive
            if (
                chunk["chunk_index"]
                == int(compressed_data[chunk["tag"]]["last_chunk"]) + 1
            ):
                compressed_data[chunk["tag"]]["content"] += "\n" + chunk["content"]
            else:
                compressed_data[chunk["tag"]]["content"] += "\n[…]\n" + chunk["content"]
            # Update the last chunk index
            compressed_data[chunk["tag"]]["last_chunk"] = chunk["chunk_index"]

    # Save the last processed entry to the cheatsheets list
    if compressed_data:
        for key, value in compressed_data.items():
            cheatsheets.append({"tag": key, "content": value["content"]})

    return cheatsheets
