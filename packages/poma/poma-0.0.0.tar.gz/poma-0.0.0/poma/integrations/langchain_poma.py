# ---------------------------------------------------------------------
#  POMA integration for LangChain
# ---------------------------------------------------------------------

import os
import hashlib
from typing import Any
from pathlib import Path
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain.document_loaders.base import BaseLoader
from langchain.schema import Document
from langchain.schema.retriever import BaseRetriever
from langchain_core.vectorstores import VectorStore
from langchain_core.callbacks.manager import CallbackManagerForRetrieverRun
from langchain_text_splitters import TextSplitter
from pydantic import Field, PrivateAttr

from poma import Poma
from poma.client import ALLOWED_FILE_EXTENSIONS
from poma.exceptions import InvalidInputError
from poma.retrieval import _cheatsheets_from_chunks

__all__ = ["PomaFileLoader", "PomaChunksetSplitter", "PomaCheatsheetRetrieverLC"]


# ------------------------------------------------------------------ #
#  Load from Path → LC Documents                                     #
# ------------------------------------------------------------------ #


class PomaFileLoader(BaseLoader):

    def __init__(self, input_path: str | Path):
        """Initialize with a file or directory path."""
        self.input_path = Path(input_path).expanduser().resolve()

    def load(self) -> list[Document]:
        """
        Load files from the input path (file or directory) into LangChain Documents.
        Only files with allowed extensions are processed; others are skipped.
        """
        path = self.input_path
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
            if file_path.suffix.lower() == ".pdf":
                page_content: str = ""  # LangChain requires str
            else:
                try:
                    page_content = file_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    skipped += 1
                    return
            documents.append(
                Document(
                    page_content=page_content,
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


class PomaChunksetSplitter(TextSplitter):

    _client: Poma = PrivateAttr()
    _show_progress: bool = PrivateAttr(default=False)

    def __init__(self, client: Poma, *, verbose: bool = False, **kwargs):
        """Initialize with a Poma client and optional verbosity."""
        super().__init__(**kwargs)
        self._client = client
        self._show_progress = bool(verbose)

    def split_text(self, text: str) -> list[str]:
        """Not implemented, use split_documents()."""
        raise NotImplementedError("Not implemented, use split_documents().")

    def split_documents(self, documents: Iterable[Document]) -> list[Document]:
        """
        Split LangChain Documents into chunkset Documents via POMA API.
        Each output Document corresponds to a chunkset, with associated chunks in metadata.
        """
        documents = list(documents)
        if not documents:
            raise InvalidInputError("No documents provided to split.")

        total_docs = len(documents)
        chunked_docs: list[Document] = []
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
            poma_doc: Document, doc_idx: int
        ) -> tuple[list[Document], str | None]:
            """Process a single document via POMA API, return chunked Documents or failed source path."""
            try:
                doc_id, src_path = _doc_id_and_src(poma_doc)
                path_obj = None
                if src_path and src_path.strip() and isinstance(src_path, str):
                    try:
                        path = Path(src_path).resolve()
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
                if self._show_progress:
                    print(
                        f"[{doc_idx}/{total_docs}] ⏳ Job {job_id} started for: {src_path}. Polling for results..."
                    )
                result = self._client.get_chunk_result(
                    str(job_id), show_progress=self._show_progress
                )
                chunks: list[dict] = result.get("chunks", [])
                chunksets: list[dict] = result.get("chunksets", [])
            except Exception as exception:
                print(
                    f"[{doc_idx}/{total_docs}] ❌ Exception chunking document: {exception}"
                )
                src_path = poma_doc.metadata.get("source_path", "in-memory-text")
                return [], src_path

            file_docs: list[Document] = []
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
                    file_docs.append(
                        Document(
                            page_content=cs.get("contents", ""),
                            metadata={
                                "doc_id": doc_id,
                                "chunkset_index": chunkset_index,
                                "chunkset": cs,
                                "chunks": relevant_chunks,
                                "source_path": src_path,
                            },
                        )
                    )
            except Exception as exception:
                print(
                    f"[{doc_idx}/{total_docs}] ❌ Exception processing chunking result: {exception}"
                )
                src_path = poma_doc.metadata.get("source_path", "in-memory-text")
                return [], src_path
            return file_docs, None

        # parallel processing of documents
        cores = os.cpu_count() or 1
        group_size = 5 if cores >= 5 else cores
        for start in range(0, total_docs, group_size):
            batch = list(
                enumerate(documents[start : start + group_size], start=start + 1)
            )
            with ThreadPoolExecutor(max_workers=group_size) as executor:
                futures = {
                    executor.submit(_process_one, doc, idx): (idx, doc)
                    for idx, doc in batch
                }
                for future in as_completed(futures):
                    idx, doc = futures[future]
                    try:
                        doc_as_chunk, failed_src = future.result()
                        if failed_src is None:
                            chunked_docs.extend(doc_as_chunk)
                            if self._show_progress:
                                src_path = doc.metadata.get(
                                    "source_path", "in-memory-text"
                                )
                                print(
                                    f"[{idx}/{total_docs}] ✅ Done: {src_path} (+{len(doc_as_chunk)} doc-chunks)"
                                )
                        else:
                            failed_paths.append(failed_src)
                            if self._show_progress:
                                print(f"[{idx}/{total_docs}] ❌ Failed: {failed_src}")
                    except Exception as error:
                        failed_paths.append(
                            doc.metadata.get("source_path", "in-memory-text")
                        )
                        if self._show_progress:
                            print(
                                f"[{idx}/{total_docs}] ❌ Failed with unexpected error: {error}"
                            )

        if failed_paths:
            print("The following files failed to process:")
            for path in failed_paths:
                print(f" - {path}")

        if not chunked_docs:
            raise InvalidInputError("No documents could be split successfully.")

        return chunked_docs


# ------------------------------------------------------------------ #
#  Cheatsheet retriever                                              #
# ------------------------------------------------------------------ #


class PomaCheatsheetRetrieverLC(BaseRetriever):

    tags: list[str] | None = Field(default=None)
    metadata: dict[str, Any] | None = Field(default=None)

    _vector_store: VectorStore = PrivateAttr()
    _top_k: int = PrivateAttr()

    def __init__(
        self,
        vector_store: VectorStore,
        *,
        top_k: int = 6,
        **kwargs,
    ):
        """Initialize with a VectorStore and number of top_k results to retrieve."""
        super().__init__(**kwargs)
        self._vector_store = vector_store
        self._top_k = top_k

    def _retrieve(self, query: str) -> list[Document]:
        """Retrieve chunkset documents and generate cheatsheets for the given query."""
        hits = self._vector_store.similarity_search(query, k=self._top_k)
        if not hits:
            return []
        grouped: dict[str, list[Document]] = {}
        for doc in hits:
            doc_id = doc.metadata["doc_id"]
            grouped.setdefault(doc_id, []).append(doc)
        cheatsheet_docs: list[Document] = []
        for doc_id, chunked_docs in grouped.items():
            cheatsheet = self._create_cheatsheet_langchain(chunked_docs)
            cheatsheet_docs.append(
                Document(page_content=cheatsheet, metadata={"doc_id": doc_id})
            )
        return cheatsheet_docs

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        """Retrieve relevant documents with callback management."""
        try:
            documents = self._retrieve(query)
            run_manager.on_retriever_end(documents)
            return documents
        except Exception as exception:
            run_manager.on_retriever_error(exception)
            raise

    def _create_cheatsheet_langchain(self, chunked_docs: list[Document]) -> str:
        """Generate a single deduplicated cheatsheet from chunked documents."""
        all_chunks = []
        seen = set()
        for doc in chunked_docs:
            doc_id = doc.metadata.get("doc_id", "unknown_doc")
            for chunk in doc.metadata.get("chunks", []):
                if not isinstance(chunk, dict):
                    continue
                chunk_index = chunk["chunk_index"]
                if chunk_index not in seen:
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
