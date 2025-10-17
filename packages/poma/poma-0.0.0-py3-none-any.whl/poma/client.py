# client.py
import os
import httpx
import zipfile
import io
import json
import time
from pathlib import Path
from typing import Any

from poma.exceptions import AuthenticationError, InvalidInputError, RemoteServerError, InvalidResponseError
from poma.retrieval import generate_cheatsheets, generate_single_cheatsheet

USER_AGENT = "poma-ai-sdk/0.1.0"

ALLOWED_FILE_EXTENSIONS: set[str] = {
    ".txt",
    ".md",
    ".html",
    ".htm",
    ".pdf",
}

API_BASE_URL = "https://api.poma-ai.com/api/v1"


class Poma:
    """
    Client for interacting with the POMA API.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        timeout: float = 600.0,
        client: httpx.Client | None = None,
    ):
        """
        Initialize the POMA client.
        Args:
            api_key (str, optional):
                API key for authenticating with POMA. If not provided,
                the value is read from the environment variable `POMA_API_KEY`.
            timeout (float, default=600.0):
                Timeout (in seconds) for all HTTP requests.
            client (httpx.Client, optional):
                Custom HTTP client. If not provided, a default client is created.
        """
        api_base_url = API_BASE_URL
        # Override API base URL if environment variable is set
        if os.environ.get("API_BASE_URL"):
            api_base_url = os.environ.get("API_BASE_URL")

        self.base_api_url = api_base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=timeout,
                                                headers={"user-agent": USER_AGENT})
        if not (api_key := api_key or os.environ.get("POMA_API_KEY", "")):
            raise Exception("POMA_API_KEY environment variable not set.")
        self._client.headers.update({"Authorization": f"Bearer {api_key}"})

    def start_chunk_file(
        self,
        file_path: os.PathLike[str],
        *,
        base_url: str | None = None,
    ) -> dict[str, Any]:
        """
        Submit a file with text to POMA for chunking.
        Args:
            file_path (os.PathLike[str]):
                Path to the input file. Must have an allowed file extension.
            base_url (str, optional):
                Optional base URL to resolve relative links within the file.
        Returns:
            A dictionary containing a unique job identifier for the submitted job.
        """
        if not file_path or not isinstance(file_path, os.PathLike):
            raise ValueError("file_path must be a non-empty os.PathLike.")
        file_extension = Path(file_path).suffix.lower()
        if file_extension not in ALLOWED_FILE_EXTENSIONS:
            raise InvalidInputError(
                f"File extension of {file_path} is not allowed; use one of the following types: {', '.join(sorted(ALLOWED_FILE_EXTENSIONS))}."
            )
        payload = {}
        if base_url:
            payload["base_url"] = base_url
        try:
            response = self._client.post(
                f"{self.base_api_url}/ingest",
                data=payload,
                files={
                    "file": (Path(file_path).name, Path(file_path).read_bytes()),
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            status = error.response.status_code
            if status in (401, 403):
                raise AuthenticationError(response.text) from error
            raise RemoteServerError(f"{status}: {response.text}") from error
        try:
            data = response.json()
        except ValueError as error:
            raise InvalidResponseError("Server returned non-JSON or empty body") from error
        return data

    def get_chunk_result(
        self,
        job_id: str,
        *,
        initial_delay: float = 5.0,
        poll_interval: float = 3.0,
        max_interval: float = 15.0,
        show_progress: bool = False,
        download_dir: str | os.PathLike[str] | None = None,
    ) -> dict[str, Any]:
        """
        Poll POMA for the result of a chunking job until completion.
        Args:
            job_id (str):
                The unique identifier of the submitted job.
            initial_delay (float, default=5.0):
                Initial delay (in seconds) before the first poll request.
            poll_interval (float, default=1.0):
                Starting interval (in seconds) between polling requests.
            max_interval (float, default=15.0):
                Maximum interval (in seconds) between polling requests.
            show_progress (bool, default=False):
                If True, logs progress messages during polling.
            download_dir (str | os.PathLike[str], optional):
                Directory to save the downloaded file in. Required if return_bytes=False.
            return_bytes (bool, default=False):
                If True, returns the file content as bytes instead of saving to disk.
        Returns:
            The JSON result containing at least the keys `chunks` and `chunksets`.

        """
        time.sleep(initial_delay)
        current_interval = poll_interval
        while True:
            time.sleep(current_interval)
            try:
                response = self._client.get(f"{self.base_api_url}/jobs/{job_id}/status")
                response.raise_for_status()
                data = response.json()
                status = data.get("status", "")
                if status == "done":
                    download = data.get("download", {})
                    download_url = download.get("download_url", "")
                    if not download_url:
                        raise RuntimeError("Failed to receive download URL from server.")

                    if download_dir is None:
                        # Return bytes content instead of saving to file
                        file_bytes = self.download_bytes(download_url)
                        return self.extract_chunks_and_chunksets_from_poma_archive(poma_archive_data=file_bytes)
                    else:
                        # Save downloaded file to directory
                        filename = download.get("filename", "downloaded_file.poma")
                        downloaded_file_path = self.download_file(download_url,
                                                                    filename,
                                                                    save_directory=download_dir)
                        return self.extract_chunks_and_chunksets_from_poma_archive(poma_archive_path=downloaded_file_path)
                elif status == "failed":
                    error_code = data.get("code", "unknown")
                    error_details = data.get("error", "No details provided.")
                    error_message = (
                        f"Job failed with code {error_code}: {error_details}"
                    )
                    raise RemoteServerError(
                        f"Job failed: {data.get('error', error_message)}"
                    )
                elif status == "processing":
                    if show_progress:
                        print(f"Job {job_id} is still processing...")
                    current_interval = min(current_interval * 1.5, max_interval)
                else:
                    raise InvalidResponseError(f"Unexpected job status: {status}")
            except httpx.HTTPStatusError as error:
                raise RemoteServerError(
                    f"HTTP error: {error.response.status_code} {error.response.text}"
                ) from error
            except Exception as error:
                raise RuntimeError(f"POMA-AI job polling failed: {error}") from error

    def extract_chunks_and_chunksets_from_poma_archive(
        self,
        poma_archive_data: bytes | None = None,
        poma_archive_path: str | os.PathLike[str] | None = None,
    ) -> dict[str, Any]:
        """
        Extract POMA archive file.
        POMA archive file is a zip file containing the chunks.json and chunksets.json files.
        Args:
            poma_archive (bytes): The POMA archive file.
        Returns:
            dict: A dictionary containing the chunks and chunksets.
        """
        # Sanity check for parameters
        if not poma_archive_data and not poma_archive_path:
            raise ValueError("Either poma_archive_data or poma_archive_path must be provided.")

        # Load the chunks and chunksets from POMA archive
        chunks = None
        chunksets = None
        if poma_archive_path:
            with zipfile.ZipFile(poma_archive_path, "r") as zip_ref:
                chunks = zip_ref.read('chunks.json')
                chunksets = zip_ref.read('chunksets.json')
        else:
            with zipfile.ZipFile(io.BytesIO(poma_archive_data), "r") as zip_ref:
                chunks = zip_ref.read('chunks.json')
                chunksets = zip_ref.read('chunksets.json')

        # Sanity check
        if not chunks or not chunksets:
            raise KeyError(
                "Result must contain 'chunks' and 'chunksets' keys."
            )

        # Load the chunks and chunksets
        json_result = {
            "chunks": json.loads(chunks),
            "chunksets": json.loads(chunksets)
        }
        return json_result

    def create_cheatsheet(
        self,
        relevant_chunksets: list[dict[str, Any]],
        all_chunks: list[dict[str, Any]],
    ) -> str:
        """
        Generates a single cheatsheet for one single document
        from relevant chunksets (relevant for a certain query)
        and from all available chunks (which must contain the textual content).
        Args:
            relevant_chunksets (list[dict]): A list of chunksets, each containing a "chunks" key with a list of chunk IDs.
            all_chunks (list[dict]): A list of all available chunk dictionaries, each representing a chunk of content.
        Returns:
            str: The textual content of the generated cheatsheet.
        """
        return generate_single_cheatsheet(relevant_chunksets, all_chunks)

    def create_cheatsheets(
        self,
        relevant_chunksets: list[dict[str, Any]],
        all_chunks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Generates cheatsheets from relevant chunksets (relevant for a certain query)
        and from all available chunks (which must contain the textual content).
        One cheatsheet is created for each document tag found in the chunks.
        Args:
            relevant_chunksets (list[dict]): A list of chunksets, each containing a "chunks" key with a list of chunk IDs.
            all_chunks (list[dict]): A list of all available chunk dictionaries, each representing a chunk of content.
        Returns:
            list[dict]: A list of dictionaries representing the generated cheatsheets, each containing:
                - 'tag': The tag associated with the respective document.
                - 'content': The textual content of the generated cheatsheet.
        """
        return generate_cheatsheets(relevant_chunksets, all_chunks)

    def download_file(
        self,
        download_url: str,
        filename: str | None = None,
        *,
        save_directory: str | os.PathLike[str] | None = None,
    ) -> str:
        """
        Download a file from the given download URL.
        Args:
            download_url (str):
                The URL to download the file from.
            filename (str, optional):
                The filename to save the file as. If not provided, will be extracted from URL.
            save_directory (str | os.PathLike[str], optional):
                Directory to save the file in. If not provided, saves to current directory.
        Returns:
            str: The path to the downloaded file.
        """
        if not download_url:
            raise ValueError("download_url cannot be empty")
        
        # Determine filename
        if not filename:
            filename = Path(download_url).name or "downloaded_file"

        # Determine save directory
        if save_directory:
            save_path = Path(save_directory) / filename
        else:
            save_path = Path(filename)

        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Download the file data
        content = self.download_bytes(download_url)

        # Save the file
        with open(save_path, "wb") as f:
            f.write(content)
        return save_path

    def download_bytes(
        self,
        download_url: str,
    ) -> bytes:
        """
        Download a file from the given download URL and return the bytes content.
        Args:
            download_url (str):
                The URL to download the file from.
        Returns:
            bytes: The content of the downloaded file as bytes.
        """
        if not download_url:
            raise ValueError("download_url cannot be empty")
        
        # Construct the full URL if it's a relative path
        if download_url.startswith("/"):
            full_url = f"{self.base_api_url}{download_url}"
        else:
            full_url = download_url
        
        print("Downloading file from:", full_url)
        try:
            # Download the file
            response = self._client.get(full_url)
            response.raise_for_status()
            
            # Return the bytes content
            return response.content
            
        except httpx.HTTPStatusError as error:
            status = error.response.status_code
            if status in (401, 403):
                raise AuthenticationError(f"Authentication failed when downloading file: {response.text}") from error
            raise RemoteServerError(f"Failed to download file: {status} {response.text}") from error
        except Exception as error:
            raise RuntimeError(f"File download failed: {error}") from error

    def close(self):
        self._client.close()

    def __enter__(self) -> "Poma":
        return self

    def __exit__(self, *exc):
        self.close()
