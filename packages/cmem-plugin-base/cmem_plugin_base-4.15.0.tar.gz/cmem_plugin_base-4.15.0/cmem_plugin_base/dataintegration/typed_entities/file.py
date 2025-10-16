"""File entities"""

import gzip
import io
import zipfile
from abc import abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import IO

from cmem.cmempy.workspace.projects.resources.resource import get_resource_response

from cmem_plugin_base.dataintegration.entity import Entity, EntityPath
from cmem_plugin_base.dataintegration.typed_entities import instance_uri, path_uri, type_uri
from cmem_plugin_base.dataintegration.typed_entities.typed_entities import (
    TypedEntitySchema,
)


def _is_gzip(stream: io.BufferedReader) -> bool:
    """Check if a stream contains gzip-compressed data."""
    head = stream.read(2)
    stream.seek(0)
    return head == b"\x1f\x8b"


def _prepare_stream_for_processing(
    input_stream: IO[bytes],
) -> tuple[io.TextIOWrapper | IO[bytes], bool]:
    """Prepare a file stream for processing.

    This utility function:
    1. Detects if the stream is gzip compressed
    2. Decompresses if needed
    3. Detects if the content is text or binary
    4. Returns appropriate stream wrapper

    Args:
        input_stream: The input stream to process (should be in binary mode)

    Returns:
        A tuple containing:
        - The processed stream (TextIOWrapper for text, original stream for binary)
        - Boolean indicating if the content is text (True) or binary (False)

    """
    buffered = io.BufferedReader(input_stream)  # type: ignore[type-var]

    decompressed_stream = gzip.GzipFile(fileobj=buffered) if _is_gzip(buffered) else buffered  # type: ignore[arg-type]

    sample = decompressed_stream.read(1024)
    decompressed_stream.seek(0)

    try:
        sample.decode("utf-8")
        is_text = True
        stream_for_processing = io.TextIOWrapper(decompressed_stream, encoding="utf-8")
    except UnicodeDecodeError:
        is_text = False
        stream_for_processing = decompressed_stream  # type: ignore[assignment]

    return stream_for_processing, is_text


class _TextToBytesWrapper:
    """Helper class to wrap a text stream and provide a bytes interface."""

    def __init__(self, text_stream: io.TextIOWrapper) -> None:
        self._text_stream = text_stream

    def read(self, size: int = -1) -> bytes:
        """Read and encode text as bytes."""
        text_content = self._text_stream.read(size)
        return text_content.encode("utf-8") if text_content else b""

    def readline(self, size: int = -1) -> bytes:
        """Read a line and encode as bytes."""
        text_line = self._text_stream.readline(size)
        return text_line.encode("utf-8") if text_line else b""

    def __iter__(self) -> Iterator[bytes]:
        """Iterate over lines as bytes."""
        for line in self._text_stream:
            yield line.encode("utf-8")

    def close(self) -> None:
        """Close the underlying text stream."""
        self._text_stream.close()

    def __enter__(self) -> "_TextToBytesWrapper":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class File:
    """A file entity that can be held in a FileEntitySchema.

    :param path: The file path.
    :param file_type: The type of the file (one of: "Local", "Project").
    :param mime: The MIME type of the file, if known.
    :param entry_path: If the file path points to a archive, the entry within the archive.
    """

    def __init__(self, path: str, file_type: str, mime: str | None, entry_path: str | None) -> None:
        self.path = path
        self.file_type = file_type
        self.mime = mime
        self.entry_path = entry_path

    @abstractmethod
    def read_stream(self, project_id: str) -> IO[bytes]:
        """Open the referenced file as a stream.

        Returns a file-like object (stream) in binary mode.
        Caller is responsible for closing the stream.
        """

    def is_text(self, project_id: str) -> bool:
        """Check if the file contains text data.

        Returns True if the file content can be decoded as UTF-8 text, False otherwise.
        This method automatically handles gzip decompression if needed.
        """
        with self.read_stream(project_id) as stream:
            _, is_text = _prepare_stream_for_processing(stream)
            return is_text

    def is_bytes(self, project_id: str) -> bool:
        """Check if the file contains binary data.

        Returns True if the file content is binary (cannot be decoded as UTF-8), False otherwise.
        This method automatically handles gzip decompression if needed.
        """
        return not self.is_text(project_id)

    def read_text(self, project_id: str) -> str:
        """Read the file content as text.

        Returns the file content as a string. Automatically handles gzip decompression if needed.
        Raises UnicodeDecodeError if the file content is not valid UTF-8 text.
        """
        with self.read_stream(project_id) as stream:
            processed_stream, is_text = _prepare_stream_for_processing(stream)
            if not is_text:
                raise UnicodeDecodeError("utf-8", b"", 0, 0, "File content is not valid UTF-8 text")
            return processed_stream.read()  # type: ignore[return-value]

    def read_bytes(self, project_id: str) -> bytes:
        """Read the file content as bytes.

        Returns the file content as bytes. Automatically handles gzip decompression if needed.
        """
        with self.read_stream(project_id) as stream:
            processed_stream, is_text = _prepare_stream_for_processing(stream)
            if is_text:
                content = processed_stream.read()  # type: ignore[attr-defined]
                return content.encode("utf-8") if isinstance(content, str) else content
            return processed_stream.read()  # type: ignore[return-value]

    @contextmanager
    def text_stream(self, project_id: str) -> Iterator[io.TextIOWrapper]:
        """Get a text stream for memory-efficient processing.

        Returns a context manager that yields a text stream for reading file content.
        Automatically handles gzip decompression if needed.
        Raises UnicodeDecodeError if the file content is not valid UTF-8 text.

        Example:
            ```python
            with file.text_stream(project_id) as stream:
                for line in stream:
                    process_line(line)
            ```

        """
        with self.read_stream(project_id) as raw_stream:
            processed_stream, is_text = _prepare_stream_for_processing(raw_stream)
            if not is_text:
                raise UnicodeDecodeError("utf-8", b"", 0, 0, "File content is not valid UTF-8 text")
            yield processed_stream  # type: ignore[misc]

    @contextmanager
    def bytes_stream(self, project_id: str) -> Iterator[IO[bytes]]:
        """Get a binary stream for memory-efficient processing.

        Returns a context manager that yields a binary stream for reading file content.
        Automatically handles gzip decompression if needed.

        Example:
            ```python
            with file.bytes_stream(project_id) as stream:
                while chunk := stream.read(8192):
                    process_chunk(chunk)
            ```

        """
        with self.read_stream(project_id) as raw_stream:
            processed_stream, is_text = _prepare_stream_for_processing(raw_stream)
            if is_text:
                # Convert text stream back to bytes for consistent API
                text_stream = processed_stream  # type: ignore[assignment]
                # Create a bytes stream by encoding the text stream
                yield _TextToBytesWrapper(text_stream)  # type: ignore[arg-type,misc]
            else:
                yield processed_stream  # type: ignore[misc]


class LocalFile(File):
    """A file that's located on the local file system."""

    def __init__(self, path: str, mime: str | None = None, entry_path: str | None = None) -> None:
        super().__init__(path, "Local", mime, entry_path)

    def read_stream(self, project_id: str) -> IO[bytes]:
        """Open the referenced file as a stream.

        Returns a file-like object (stream) in binary mode.
        Caller is responsible for closing the stream.
        """
        if self.entry_path:
            archive = zipfile.ZipFile(self.path, "r")
            try:
                return archive.open(self.entry_path, "r")
            except KeyError as err:
                archive.close()
                raise FileNotFoundError(
                    f"Entry '{self.entry_path}' not found in archive '{self.path}'."
                ) from err
        else:
            if not Path(self.path).is_file():
                raise FileNotFoundError(f"File '{self.path}' does not exist.")
            return Path(self.path).open("rb")


class ProjectFile(File):
    """A project file"""

    def __init__(self, path: str, mime: str | None = None, entry_path: str | None = None) -> None:
        super().__init__(path, "Project", mime, entry_path)

    def read_stream(self, project_id: str) -> IO[bytes]:
        """Open the referenced file as a stream.

        Returns a file-like object (stream) in binary mode.
        Caller is responsible for closing the stream.
        """
        response = get_resource_response(project_id, self.path)
        if response.status_code != 200:  # noqa: PLR2004
            raise FileNotFoundError(f"Project file '{self.path}' not found.")
        response_bytes = BytesIO(response.raw.read())
        if self.entry_path:
            archive = zipfile.ZipFile(response_bytes, "r")
            try:
                return archive.open(self.entry_path, "r")
            except KeyError as err:
                archive.close()
                raise FileNotFoundError(
                    f"Entry '{self.entry_path}' not found in project file '{self.path}'."
                ) from err
        else:
            return response_bytes


class FileEntitySchema(TypedEntitySchema[File]):
    """Entity schema that holds a collection of files."""

    def __init__(self):
        # The parent class TypedEntitySchema implements a singleton pattern
        if not hasattr(self, "_initialized"):
            super().__init__(
                type_uri=type_uri("File"),
                paths=[
                    EntityPath(path_uri("filePath"), is_single_value=True),
                    EntityPath(path_uri("fileType"), is_single_value=True),
                    EntityPath(path_uri("mimeType"), is_single_value=True),
                    EntityPath(path_uri("entryPath"), is_single_value=True),
                ],
            )

    def to_entity(self, value: File) -> Entity:
        """Create a generic entity from a file"""
        return Entity(
            uri=instance_uri(value.path),
            values=[
                [value.path],
                [value.file_type],
                [value.mime] if value.mime else [],
                [value.entry_path] if value.entry_path else [],
            ],
        )

    def from_entity(self, entity: Entity) -> File:
        """Create a file entity from a generic entity."""
        path = entity.values[0][0]
        file_type = entity.values[1][0]
        mime = entity.values[2][0] if entity.values[2] and entity.values[2][0] else None
        entry_path = entity.values[3][0] if entity.values[3] and entity.values[3][0] else None

        match file_type:
            case "Local":
                return LocalFile(path, mime, entry_path)
            case "Project":
                return ProjectFile(path, mime, entry_path)
            case _:
                raise ValueError(f"File '{path}' has unexpected type '{file_type}'.")
