# ---------------------------------------------------------------------
#  POMA integration for LlamaIndex
# ---------------------------------------------------------------------

import os
import hashlib
from typing import Any
from pathlib import Path
from collections import defaultdict
from collections.abc import Sequence, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed

from llama_index.core.readers.base import BaseReader
from llama_index.core.node_parser import NodeParser
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import (
    Document,
    NodeWithScore,
    TextNode,
    BaseNode,
    QueryBundle,
)
from pydantic import PrivateAttr

from poma import Poma
from poma.client import ALLOWED_FILE_EXTENSIONS
from poma.retrieval import _cheatsheets_from_chunks
from poma.exceptions import InvalidInputError

__all__ = ["PomaFileReader", "PomaChunksetNodeParser", "PomaCheatsheetRetrieverLI"]


# ------------------------------------------------------------------ #
#  Load from Path → LI Documents                                     #
# ------------------------------------------------------------------ #


class PomaFileReader(BaseReader):

    def load_data(self, input_path: str | Path) -> list[Document]:
        """
        Load files from the input path (file or directory) into LlamaIndex Documents.
        Only files with allowed extensions are processed; others are skipped.
        """
        path = Path(input_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"No such path: {path}")

        documents: list[Document] = []
        skipped: int = 0

        def _process_file(file_path: Path):
            nonlocal skipped, documents
            if not file_path.is_file():
                return
            file_extension = file_path.suffix.lower()
            if not file_extension or file_extension not in ALLOWED_FILE_EXTENSIONS:
                skipped += 1
                return
            file_bytes = file_path.read_bytes()
            file_hash = hashlib.md5(file_bytes).hexdigest()
            if file_extension == ".pdf":
                # LlamaIndex requires `text` to be str.
                # Actual file processing happens downstream in the node parser.
                text_payload: str = ""
            else:
                try:
                    text_payload = file_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    skipped += 1
                    return
            documents.append(
                Document(
                    text=text_payload,
                    metadata={
                        "source_path": str(file_path),
                        "doc_id": f"{file_hash}",
                    },
                )
            )

        if path.is_file():
            _process_file(path)
        elif path.is_dir():
            for path_in_dir in sorted(path.rglob("*")):
                _process_file(path_in_dir)
        else:
            raise FileNotFoundError(f"Unsupported path type (not file/dir): {path}")

        allowed = ", ".join(sorted(ALLOWED_FILE_EXTENSIONS))
        if not documents:
            raise InvalidInputError(f"No supported files found. Allowed: {allowed}")
        if skipped > 0:
            print(
                f"Skipped {skipped} file(s) due to unsupported or unreadable type. Allowed: {allowed}"
            )
        return documents


# ------------------------------------------------------------------ #
#  Generate Chunksets                                                #
# ------------------------------------------------------------------ #


class PomaChunksetNodeParser(NodeParser):
    # """Calls **POMA API** for each document, choosing text vs file ingestion as needed."""

    _client: Poma = PrivateAttr()

    def __init__(self, *, client: Poma):
        """Initialize with Poma client instance."""
        super().__init__()
        self._client = client

    def _parse_nodes(
        self, nodes: Sequence[BaseNode], show_progress: bool = False, **kwargs: Any
    ) -> list[BaseNode]:
        """Not implemented, use _get_nodes_from_documents()."""
        raise NotImplementedError("Not implemented, use _get_nodes_from_documents().")

    def _get_nodes_from_documents(
        self, documents: Sequence[Document], show_progress: bool = False
    ) -> list[BaseNode]:
        """
        Convert LlamaIndex Documents into chunkset Nodes via POMA API.
        Each output Node represents a chunkset, with associated chunks in metadata.
        """

        documents = list(documents)
        if not documents:
            raise InvalidInputError("No documents provided to process.")

        total_docs = len(documents)
        chunked_nodes: list[BaseNode] = []
        failed_paths: list[str] = []

        def _safe_int(value: object) -> int | None:
            if isinstance(value, bool):
                return None
            if isinstance(value, int):
                return value
            if isinstance(value, str):
                try:
                    return int(value.strip())
                except Exception:
                    return None
            try:
                return int(value)  # type: ignore[arg-type]
            except Exception:
                return None

        def _doc_id_and_src(doc: Document) -> tuple[str, str]:
            src_path = doc.metadata.get("source_path", "in-memory-text")
            doc_id = doc.metadata.get("doc_id") or Path(src_path).stem or "unknown-doc"
            return doc_id, src_path

        def _process_one(
            poma_doc: Document, doc_idx: int, total_docs: int
        ) -> tuple[list[BaseNode], str | None]:
            """Process a single document via POMA API, return chunkset nodes or failed source path."""
            try:
                doc_id, src_path = _doc_id_and_src(poma_doc)
                path_obj: Path | None = None
                if src_path and src_path.strip() and isinstance(src_path, str):
                    try:
                        path = Path(src_path).expanduser().resolve()
                        if path.exists():
                            path_obj = path
                    except Exception:
                        path_obj = None
                if not path_obj:
                    raise InvalidInputError(
                        "No valid source_path found in document metadata."
                    )
                start_result = self._client.start_chunk_file(path_obj, base_url=None)
                job_id = start_result.get("job_id")
                if not job_id:
                    raise RuntimeError("Failed to receive job ID from server.")
                if show_progress:
                    print(
                        f"[{doc_idx}/{total_docs}] ⏳ Job {job_id} started for: {src_path}. Polling for results..."
                    )
                result = self._client.get_chunk_result(
                    str(job_id), show_progress=show_progress
                )
                chunks: list[dict] = result.get("chunks", [])
                chunksets: list[dict] = result.get("chunksets", [])
            except Exception as exception:
                print(
                    f"[{doc_idx}/{total_docs}] ❌ Exception chunking document: {exception}"
                )
                src_path = poma_doc.metadata.get("source_path", "in-memory-text")
                return [], src_path

            file_nodes: list[BaseNode] = []
            try:
                chunks_by_index: dict[int, dict] = {}
                for chunk in chunks:
                    idx = _safe_int(chunk.get("chunk_index"))
                    if idx is not None:
                        chunks_by_index[idx] = chunk
                for cs in chunksets:
                    chunkset_index = cs.get("chunkset_index")
                    chunks_indices = cs.get("chunks", []) or []
                    normalized_indices: list[int] = []
                    for chunk_index in chunks_indices:
                        idx = _safe_int(chunk_index)
                        if idx is not None:
                            normalized_indices.append(idx)
                    relevant_chunks = [
                        chunks_by_index[idx]
                        for idx in normalized_indices
                        if idx in chunks_by_index
                    ]
                    text_node = TextNode(
                        text=cs.get("contents", ""),
                        metadata={
                            "doc_id": doc_id,
                            "chunkset_index": chunkset_index,
                            "chunks": relevant_chunks,
                            "chunkset": cs,
                            "source_path": src_path,
                        },
                    )
                    # Keep embeddings clean – just embed content, not metadata
                    text_node.excluded_embed_metadata_keys = list(
                        text_node.metadata.keys()
                    )
                    file_nodes.append(text_node)
            except Exception as exception:
                print(
                    f"[{doc_idx}/{total_docs}] ❌ Exception processing chunking result: {exception}"
                )
                src_path = poma_doc.metadata.get("source_path", "in-memory-text")
                return [], src_path
            return file_nodes, None

        # parallel processing of documents
        cores = os.cpu_count() or 1
        group_size = 5 if cores >= 5 else cores
        for start in range(0, total_docs, group_size):
            batch = list(
                enumerate(documents[start : start + group_size], start=start + 1)
            )
            with ThreadPoolExecutor(max_workers=group_size) as executor:
                futures = {
                    executor.submit(_process_one, doc, idx, total_docs): (idx, doc)
                    for idx, doc in batch
                }
                for future in as_completed(futures):
                    idx, doc = futures[future]
                    try:
                        node_chunks, failed_src = future.result()
                        if failed_src is None:
                            chunked_nodes.extend(node_chunks)
                            if show_progress:
                                src_path = doc.metadata.get(
                                    "source_path", "in-memory-text"
                                )
                                print(
                                    f"[{idx}/{total_docs}] ✅ Done: {src_path} (+{len(node_chunks)} node-chunks)"
                                )
                        else:
                            failed_paths.append(failed_src)
                            if show_progress:
                                print(f"[{idx}/{total_docs}] ❌ Failed: {failed_src}")
                    except Exception as error:
                        failed_paths.append(
                            doc.metadata.get("source_path", "in-memory-text")
                        )
                        if show_progress:
                            print(
                                f"[{idx}/{total_docs}] ❌ Failed with unexpected error: {error}"
                            )

        if failed_paths:
            print("The following files failed to process:")
            for path in failed_paths:
                print(f" - {path}")

        if not chunked_nodes:
            raise InvalidInputError("No documents could be split successfully.")

        return chunked_nodes


# ----------------------------------------------------------------
# Cheatsheet Retriever
# ----------------------------------------------------------------


class PomaCheatsheetRetrieverLI(BaseRetriever):

    def __init__(self, base: BaseRetriever):
        """Wrap an existing LlamaIndex retriever. Keep its callback/verbosity."""
        if not isinstance(base, BaseRetriever):
            raise ValueError("base must be an instance of BaseRetriever.")
        super().__init__(
            callback_manager=getattr(base, "callback_manager", None),
            verbose=getattr(base, "_verbose", False),
        )
        self._base = base

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        """Retrieve chunkset nodes and generate cheatsheets for the given query."""
        nodes = self._base.retrieve(query_bundle)
        if not nodes:
            return []
        grouped: dict[str, list[NodeWithScore]] = defaultdict(list)
        best_score: dict[str, float] = defaultdict(float)
        for node in nodes:
            doc_id = node.metadata["doc_id"]
            grouped[doc_id].append(node)
            best_score[doc_id] = max(best_score[doc_id], node.score or 1.0)
        cheatsheet_nodes: list[NodeWithScore] = []
        for doc_id, chunked_nodes in grouped.items():
            cheatsheet = self._create_cheatsheet_llamaindex(chunked_nodes)
            cheatsheet_node = TextNode(text=cheatsheet, metadata={"doc_id": doc_id})
            cheatsheet_nodes.append(
                NodeWithScore(node=cheatsheet_node, score=best_score[doc_id])
            )
        return cheatsheet_nodes

    def as_query_engine(self, **kwargs):
        """Wrap as a LlamaIndex RetrieverQueryEngine."""
        from llama_index.core.query_engine import RetrieverQueryEngine

        return RetrieverQueryEngine(self, **kwargs)

    def _create_cheatsheet_llamaindex(self, chunked_nodes: list[NodeWithScore]) -> str:
        """Generate a single deduplicated cheatsheet from chunked nodes."""
        all_chunks = []
        seen = set()
        for node in chunked_nodes:
            doc_id = node.metadata.get("doc_id", "unknown_doc")
            chunks = node.metadata.get("chunks", [])
            if not chunks:
                continue
            for chunk in chunks:
                if not isinstance(chunk, dict):
                    continue
                chunk_index = chunk.get("chunk_index")
                if chunk_index is None or chunk_index in seen:
                    continue
                seen.add(chunk_index)
                chunk["tag"] = doc_id
                all_chunks.append(chunk)
        sorted_chunks = sorted(
            all_chunks, key=lambda chunk: (chunk["tag"], chunk["chunk_index"])
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
