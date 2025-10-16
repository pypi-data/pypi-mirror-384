from __future__ import annotations

from typing import AsyncGenerator, Iterable, Optional, Set

from remotivelabs.broker.auth import ApiKeyAuth, NoAuth
from remotivelabs.broker.recording_session import File, RecordingSessionClient
from remotivelabs.broker.recording_session.file import FileType


class RecursiveFilesListingClient:
    """
    Client for recursively listing files using a broker API.

    This class provides functionality to recursively list files and directories using
    a RecordingSessionClient. It retrieves files from specified paths and can process them
    with customizable options such as filtering by file types or including directories
    in the results.

    Attributes:
        broker_url (str): The URL of the broker API.
        api_key (Optional[str]): The API key used for authentication, if required by the
            broker API.
    """

    def __init__(self, broker_url: str, api_key: Optional[str]):
        self._broker_client = RecordingSessionClient(url=broker_url, auth=ApiKeyAuth(api_key) if api_key is not None else NoAuth())

    async def _list_files(self, path: str = "/") -> list[File]:
        return await self._broker_client.list_recording_files(path=path)

    async def list_all_files(
        self,
        path: str = "/",
        file_types: Optional[Iterable[FileType]] = None,
    ) -> list[File]:
        files: list[File] = []
        async for f in self._iter_files_recursive(root=path, return_types=file_types):
            files.append(f)
        return files

    async def _iter_files_recursive(
        self,
        root: str = "/",
        *,
        return_types: Optional[Iterable[FileType]] = None,
        include_dirs: bool = False,
    ) -> AsyncGenerator[File, None]:
        seen: Set[str] = set()

        async def _walk(path: str) -> AsyncGenerator[File, None]:
            if path in seen:
                return
            seen.add(path)

            resp = await self._list_files(path)
            for f in resp or []:
                if f.type == FileType.FILE_TYPE_FOLDER:
                    # Optionally yield the directory itself
                    if include_dirs and (return_types is None or f.type in return_types):
                        yield f
                    # Recurse into the folder
                    async for file in _walk(f.path):
                        yield file
                elif return_types is None or f.type in return_types:
                    yield f

        async for file in _walk(root):
            yield file
