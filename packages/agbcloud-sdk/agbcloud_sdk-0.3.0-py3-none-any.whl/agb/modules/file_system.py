import json
import threading
import time
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Union

from agb.api.base_service import BaseService
from agb.model.response import ApiResponse, BoolResult
from agb.logger import get_logger

logger = get_logger(__name__)


class FileChangeEvent:
    """Represents a single file change event."""

    def __init__(
        self,
        event_type: str = "",
        path: str = "",
        path_type: str = "",
    ):
        """
        Initialize a FileChangeEvent.

        Args:
            event_type (str): Type of the file change event (e.g., "modify", "create", "delete").
            path (str): Path of the file or directory that changed.
            path_type (str): Type of the path ("file" or "directory").
        """
        self.event_type = event_type
        self.path = path
        self.path_type = path_type

    def __repr__(self):
        return f"FileChangeEvent(event_type='{self.event_type}', path='{self.path}', path_type='{self.path_type}')"

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary representation."""
        return {
            "eventType": self.event_type,
            "path": self.path,
            "pathType": self.path_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "FileChangeEvent":
        """Create FileChangeEvent from dictionary."""
        return cls(
            event_type=data.get("eventType", ""),
            path=data.get("path", ""),
            path_type=data.get("pathType", ""),
        )


class FileInfoResult(ApiResponse):
    """Result of file info operations."""

    def __init__(
        self,
        request_id: str = "",
        success: bool = False,
        file_info: Optional[Dict[str, Any]] = None,
        error_message: str = "",
    ):
        """
        Initialize a FileInfoResult.

        Args:
            request_id (str, optional): Unique identifier for the API request.
                Defaults to "".
            success (bool, optional): Whether the operation was successful.
                Defaults to False.
            file_info (Dict[str, Any], optional): File information. Defaults to None.
            error_message (str, optional): Error message if the operation failed.
                Defaults to "".
        """
        super().__init__(request_id)
        self.success = success
        self.file_info = file_info or {}
        self.error_message = error_message


class DirectoryListResult(ApiResponse):
    """Result of directory listing operations."""

    def __init__(
        self,
        request_id: str = "",
        success: bool = False,
        entries: Optional[List[Dict[str, Any]]] = None,
        error_message: str = "",
    ):
        """
        Initialize a DirectoryListResult.

        Args:
            request_id (str, optional): Unique identifier for the API request.
                Defaults to "".
            success (bool, optional): Whether the operation was successful.
                Defaults to False.
            entries (List[Dict[str, Any]], optional): Directory entries. Defaults to
                None.
            error_message (str, optional): Error message if the operation failed.
                Defaults to "".
        """
        super().__init__(request_id)
        self.success = success
        self.entries = entries or []
        self.error_message = error_message


class FileContentResult(ApiResponse):
    """Result of file read operations."""

    def __init__(
        self,
        request_id: str = "",
        success: bool = False,
        content: str = "",
        error_message: str = "",
    ):
        """
        Initialize a FileContentResult.

        Args:
            request_id (str, optional): Unique identifier for the API request.
                Defaults to "".
            success (bool, optional): Whether the operation was successful.
                Defaults to False.
            content (str, optional): File content. Defaults to "".
            error_message (str, optional): Error message if the operation failed.
                Defaults to "".
        """
        super().__init__(request_id)
        self.success = success
        self.content = content
        self.error_message = error_message


class MultipleFileContentResult(ApiResponse):
    """Result of multiple file read operations."""

    def __init__(
        self,
        request_id: str = "",
        success: bool = False,
        contents: Optional[Dict[str, str]] = None,
        error_message: str = "",
    ):
        """
        Initialize a MultipleFileContentResult.

        Args:
            request_id (str, optional): Unique identifier for the API request.
                Defaults to "".
            success (bool, optional): Whether the operation was successful.
                Defaults to False.
            contents (Dict[str, str], optional): Dictionary of file paths to file
                contents. Defaults to None.
            error_message (str, optional): Error message if the operation failed.
                Defaults to "".
        """
        super().__init__(request_id)
        self.success = success
        self.contents = contents or {}
        self.error_message = error_message


class FileSearchResult(ApiResponse):
    """Result of file search operations."""

    def __init__(
        self,
        request_id: str = "",
        success: bool = False,
        matches: Optional[List[str]] = None,
        error_message: str = "",
    ):
        """
        Initialize a FileSearchResult.

        Args:
            request_id (str, optional): Unique identifier for the API request.
                Defaults to "".
            success (bool, optional): Whether the operation was successful.
                Defaults to False.
            matches (List[str], optional): Matching file paths. Defaults to None.
            error_message (str, optional): Error message if the operation failed.
                Defaults to "".
        """
        super().__init__(request_id)
        self.success = success
        self.matches = matches or []
        self.error_message = error_message


class FileChangeResult(ApiResponse):
    """Result of file change detection operations."""

    def __init__(
        self,
        request_id: str = "",
        success: bool = False,
        events: Optional[List[FileChangeEvent]] = None,
        raw_data: str = "",
        error_message: str = "",
    ):
        """
        Initialize a FileChangeResult.

        Args:
            request_id (str, optional): Unique identifier for the API request.
                Defaults to "".
            success (bool, optional): Whether the operation was successful.
                Defaults to False.
            events (List[FileChangeEvent], optional): List of file change events.
                Defaults to None.
            raw_data (str, optional): Raw response data for debugging. Defaults to "".
            error_message (str, optional): Error message if the operation failed.
                Defaults to "".
        """
        super().__init__(request_id)
        self.success = success
        self.events = events or []
        self.raw_data = raw_data
        self.error_message = error_message

    def has_changes(self) -> bool:
        """Check if there are any file changes."""
        return len(self.events) > 0

    def get_modified_files(self) -> List[str]:
        """Get list of modified file paths."""
        return [
            event.path
            for event in self.events
            if event.event_type == "modify" and event.path_type == "file"
        ]

    def get_created_files(self) -> List[str]:
        """Get list of created file paths."""
        return [
            event.path
            for event in self.events
            if event.event_type == "create" and event.path_type == "file"
        ]

    def get_deleted_files(self) -> List[str]:
        """Get list of deleted file paths."""
        return [
            event.path
            for event in self.events
            if event.event_type == "delete" and event.path_type == "file"
        ]

    def __repr__(self):
        return (
            f"FileChangeResult(success={self.success}, events_count={len(self.events)})"
        )


class FileSystem(BaseService):
    """
    FileSystem provides file system operations for the session.
    """

    # Default chunk size is 50KB
    DEFAULT_CHUNK_SIZE = 50 * 1024

    def create_directory(self, path: str) -> BoolResult:
        """
        Create a new directory at the specified path.

        Args:
            path: The path of the directory to create.

        Returns:
            BoolResult: Result object containing success status and error message if
                any.
        """
        args = {"path": path}
        try:
            result = self._call_mcp_tool("create_directory", args)
            logger.debug(f"Response from CallMcpTool - create_directory: {result}")
            if result.success:
                return BoolResult(request_id=result.request_id, success=True, data=True)
            else:
                return BoolResult(
                    request_id=result.request_id,
                    success=False,
                    error_message=result.error_message,
                )
        except Exception as e:
            return BoolResult(
                request_id="",
                success=False,
                error_message=f"Failed to create directory: {e}",
            )

    def edit_file(
        self, path: str, edits: List[Dict[str, str]], dry_run: bool = False
    ) -> BoolResult:
        """
        Edit a file by replacing occurrences of oldText with newText.

        Args:
            path: The path of the file to edit.
            edits: A list of dictionaries specifying oldText and newText.
            dry_run: If True, preview changes without applying them.

        Returns:
            BoolResult: Result object containing success status and error message if
                any.
        """
        args = {"path": path, "edits": edits, "dryRun": dry_run}
        try:
            result = self._call_mcp_tool("edit_file", args)
            logger.debug(f"Response from CallMcpTool - edit_file: {result}")
            if result.success:
                return BoolResult(request_id=result.request_id, success=True, data=True)
            else:
                return BoolResult(
                    request_id=result.request_id,
                    success=False,
                    error_message=result.error_message,
                )
        except Exception as e:
            return BoolResult(
                request_id="",
                success=False,
                error_message=f"Failed to edit file: {e}",
            )

    def get_file_info(self, path: str) -> FileInfoResult:
        """
        Get information about a file or directory.

        Args:
            path: The path of the file or directory to inspect.

        Returns:
            FileInfoResult: Result object containing file info and error message if any.
        """

        def parse_file_info(file_info_str: str) -> Dict[str, Any]:
            """
            Parse file info string into a dictionary.

            Args:
                file_info_str (str): File info string in format:
                    "key1: value1\nkey2: value2\n..."

            Returns:
                Dict[str, Any]: Dictionary containing parsed file information.
            """
            result: Dict[str, Any] = {}
            lines = file_info_str.split("\n")
            for line in lines:
                if ":" in line:
                    key, value_str = line.split(":", 1)
                    key = key.strip()
                    value_str = value_str.strip()

                    # Convert boolean values
                    value: Any = value_str
                    if value_str.lower() == "true":
                        value = True
                    elif value_str.lower() == "false":
                        value = False

                    # Convert numeric values
                    try:
                        if isinstance(value, str):
                            value = float(value) if "." in value else int(value)
                    except ValueError:
                        pass

                    result[key] = value
            return result

        args = {"path": path}
        try:
            result = self._call_mcp_tool("get_file_info", args)
            try:
                logger.debug("Response body:")
                logger.debug(
                    json.dumps(
                        getattr(result, "body", result), ensure_ascii=False, indent=2
                    )
                )
            except Exception:
                logger.debug(f"Response: {result}")
            if result.success:
                file_info = parse_file_info(result.data)
                return FileInfoResult(
                    request_id=result.request_id,
                    success=True,
                    file_info=file_info,
                )
            else:
                return FileInfoResult(
                    request_id=result.request_id,
                    success=False,
                    error_message=result.error_message or "Failed to get file info",
                )
        except Exception as e:
            return FileInfoResult(
                request_id="",
                success=False,
                error_message=f"Failed to get file info: {e}",
            )

    def list_directory(self, path: str) -> DirectoryListResult:
        """
        List the contents of a directory.

        Args:
            path: The path of the directory to list.

        Returns:
            DirectoryListResult: Result object containing directory entries and error
                message if any.
        """

        def parse_directory_listing(text) -> List[Dict[str, Union[str, bool]]]:
            """
            Parse a directory listing text into a list of file/directory entries.

            Args:
                text (str): Directory listing text in format:
                    [DIR] directory_name
                    [FILE] file_name
                    Each entry should be on a new line with [DIR] or [FILE] prefix

            Returns:
                list: List of dictionaries, each containing:
                    - name (str): Name of the file or directory
                    - isDirectory (bool): True if entry is a directory, False if file

            Example:
                Input text:
                    [DIR] folder1
                    [FILE] test.txt

                Returns:
                    [
                        {"name": "folder1", "isDirectory": True},
                        {"name": "test.txt", "isDirectory": False}
                    ]
            """
            result: List[Dict[str, Union[str, bool]]] = []
            lines = text.split("\n")

            for line in lines:
                line = line.strip()
                if line == "":
                    continue

                entry_map: Dict[str, Union[str, bool]] = {}
                if line.startswith("[DIR]"):
                    entry_map["isDirectory"] = True
                    entry_map["name"] = line.replace("[DIR]", "").strip()
                elif line.startswith("[FILE]"):
                    entry_map["isDirectory"] = False
                    entry_map["name"] = line.replace("[FILE]", "").strip()
                else:
                    # Skip lines that don't match the expected format
                    continue

                result.append(entry_map)

            return result

        args = {"path": path}
        try:
            result = self._call_mcp_tool("list_directory", args)
            try:
                logger.debug("Response body:")
                logger.debug(
                    json.dumps(
                        getattr(result, "body", result), ensure_ascii=False, indent=2
                    )
                )
            except Exception:
                logger.debug(f"Response: {result}")
            if result.success:
                entries = parse_directory_listing(result.data)
                return DirectoryListResult(
                    request_id=result.request_id, success=True, entries=entries
                )
            else:
                return DirectoryListResult(
                    request_id=result.request_id,
                    success=False,
                    error_message=result.error_message or "Failed to list directory",
                )
        except Exception as e:
            return DirectoryListResult(
                request_id="",
                success=False,
                error_message=f"Failed to list directory: {e}",
            )

    def move_file(self, source: str, destination: str) -> BoolResult:
        """
        Move a file or directory from source path to destination path.

        Args:
            source: The source path of the file or directory.
            destination: The destination path.

        Returns:
            BoolResult: Result object containing success status and error message if
                any.
        """
        args = {"source": source, "destination": destination}
        try:
            result = self._call_mcp_tool("move_file", args)
            logger.debug(f"Response from CallMcpTool - move_file: {result}")
            if result.success:
                return BoolResult(request_id=result.request_id, success=True, data=True)
            else:
                return BoolResult(
                    request_id=result.request_id,
                    success=False,
                    error_message=result.error_message or "Failed to move file",
                )
        except Exception as e:
            return BoolResult(
                request_id="",
                success=False,
                error_message=f"Failed to move file: {e}",
            )

    def _read_file_chunk(
        self, path: str, offset: int = 0, length: int = 0
    ) -> FileContentResult:
        """
        Read the contents of a file (internal function for chunked reading).

        Args:
            path: The path of the file to read.
            offset: Byte offset to start reading from (0-based).
            length: Number of bytes to read. If 0, reads the entire file from offset.

        Returns:
            FileContentResult: Result object containing file content and error message
                if any.
        """
        args: Dict[str, Union[str, int]] = {"path": path}
        if offset > 0:
            args["offset"] = offset
        if length > 0:
            args["length"] = length

        try:
            result = self._call_mcp_tool("read_file", args)
            try:
                logger.debug("Response body:")
                logger.debug(
                    json.dumps(
                        getattr(result, "body", result), ensure_ascii=False, indent=2
                    )
                )
            except Exception:
                logger.debug(f"Response: {result}")
            if result.success:
                return FileContentResult(
                    request_id=result.request_id,
                    success=True,
                    content=result.data,
                )
            else:
                return FileContentResult(
                    request_id=result.request_id,
                    success=False,
                    error_message=result.error_message or "Failed to read file",
                )
        except Exception as e:
            return FileContentResult(
                request_id="",
                success=False,
                error_message=f"Failed to read file: {e}",
            )

    def _write_file_chunk(
        self, path: str, content: str, mode: str = "overwrite"
    ) -> BoolResult:
        """
        Write content to a file (internal function for chunked writing).

        Args:
            path: The path of the file to write.
            content: The content to write to the file.
            mode: The write mode ("overwrite" or "append").

        Returns:
            BoolResult: Result object containing success status and error message if
                any.
        """
        if mode not in ["overwrite", "append"]:
            return BoolResult(
                request_id="",
                success=False,
                error_message=(
                    f"Invalid write mode: {mode}. Must be 'overwrite' or " "'append'."
                ),
            )

        args = {"path": path, "content": content, "mode": mode}
        try:
            result = self._call_mcp_tool("write_file", args)
            logger.debug(f"Response from CallMcpTool - write_file: {result}")
            if result.success:
                return BoolResult(request_id=result.request_id, success=True, data=True)
            else:
                return BoolResult(
                    request_id=result.request_id,
                    success=False,
                    error_message=result.error_message or "Failed to write file",
                )
        except Exception as e:
            return BoolResult(
                request_id="",
                success=False,
                error_message=f"Failed to write file: {e}",
            )

    def read_file(self, path: str) -> FileContentResult:
        """
        Read the contents of a file.

        Args:
            path: The path of the file to read.

        Returns:
            FileContentResult: Result object containing file content and error message
                if any.
        """
        try:
            # Get file info to check size
            file_info_result = self.get_file_info(path)
            if not file_info_result.success:
                return FileContentResult(
                    request_id=file_info_result.request_id,
                    success=False,
                    error_message=file_info_result.error_message,
                )

            # Check if file exists and is a file (not a directory)
            if not file_info_result.file_info or file_info_result.file_info.get(
                "isDirectory", False
            ):
                return FileContentResult(
                    request_id=file_info_result.request_id,
                    success=False,
                    error_message=f"Path does not exist or is a directory: {path}",
                )

            # If the file is empty, return empty string
            file_size = file_info_result.file_info.get("size", 0)
            if file_size == 0:
                return FileContentResult(
                    request_id=file_info_result.request_id,
                    success=True,
                    content="",
                )

            # Read the file in chunks
            content = []
            offset = 0
            chunk_count = 0
            while offset < file_size:
                length = min(self.DEFAULT_CHUNK_SIZE, file_size - offset)
                chunk_result = self._read_file_chunk(path, offset, length)
                logger.debug(
                    f"ReadFile: Reading chunk {chunk_count + 1} "
                    f"({length} bytes at offset {offset}/{file_size})"
                )

                if not chunk_result.success:
                    return chunk_result  # Return the error

                content.append(chunk_result.content)
                offset += length
                chunk_count += 1

            return FileContentResult(
                request_id=file_info_result.request_id,
                success=True,
                content="".join(content),
            )

        except Exception as e:
            return FileContentResult(
                request_id="",
                success=False,
                error_message=f"Failed to read file: {e}",
            )

    def write_file(
        self, path: str, content: str, mode: str = "overwrite"
    ) -> BoolResult:
        """
        Write content to a file. Automatically handles large files by chunking.

        Args:
            path: The path of the file to write.
            content: The content to write to the file.
            mode: The write mode ("overwrite" or "append").

        Returns:
            BoolResult: Result object containing success status and error message if
                any.
        """
        content_len = len(content)
        logger.info(
            f"WriteFile: Starting chunked write to {path} (total size: "
            f"{content_len} bytes, chunk size: {self.DEFAULT_CHUNK_SIZE} bytes)"
        )

        # If the content length is less than the chunk size, write it directly
        if content_len <= self.DEFAULT_CHUNK_SIZE:
            return self._write_file_chunk(path, content, mode)

        try:
            # Write the first chunk (creates or overwrites the file)
            first_chunk = content[: self.DEFAULT_CHUNK_SIZE]
            result = self._write_file_chunk(path, first_chunk, mode)
            if not result.success:
                return result

            # Write the rest in chunks (appending)
            offset = self.DEFAULT_CHUNK_SIZE
            while offset < content_len:
                end = min(offset + self.DEFAULT_CHUNK_SIZE, content_len)
                current_chunk = content[offset:end]
                result = self._write_file_chunk(path, current_chunk, "append")
                if not result.success:
                    return result
                offset = end

            return BoolResult(request_id=result.request_id, success=True, data=True)

        except Exception as e:
            return BoolResult(
                request_id="",
                success=False,
                error_message=f"Failed to write file: {e}",
            )

    def read_multiple_files(self, paths: List[str]) -> MultipleFileContentResult:
        """
        Read the contents of multiple files at once.

        Args:
            paths: A list of file paths to read.

        Returns:
            MultipleFileContentResult: Result object containing a dictionary mapping
                file paths to contents,
            and error message if any.
        """

        def parse_multiple_files_response(text: str) -> Dict[str, str]:
            """
            Parse the response from reading multiple files.

            Args:
                text (str): The response string containing file contents.
                Format: "/path/to/file1.txt: Content of file1\n\n---\n
                    /path/to/file2.txt: \nContent of file2\n"

            Returns:
                Dict[str, str]: A dictionary mapping file paths to their content.
            """
            result: Dict[str, str] = {}
            if not text:
                return result

            lines = text.split("\n")
            current_path = None
            current_content = []

            for i, line in enumerate(lines):
                # Check if this line contains a file path (ends with a colon)
                if ":" in line and not current_path:
                    # Extract path (everything before the first colon)
                    path_end = line.find(":")
                    path = line[:path_end].strip()

                    # Start collecting content (everything after the colon)
                    current_path = path

                    # If there's content on the same line after the colon, add it
                    if len(line) > path_end + 1:
                        content_start = line[path_end + 1 :].strip()
                        if content_start:
                            current_content.append(content_start)

                # Check if this is a separator line
                elif line.strip() == "---":
                    # Save the current file content
                    if current_path:
                        result[current_path] = "\n".join(current_content).strip()
                        current_path = None
                        current_content = []

                # If we're collecting content for a path, add this line
                elif current_path is not None:
                    current_content.append(line)

            # Save the last file content if exists
            if current_path:
                result[current_path] = "\n".join(current_content).strip()

            return result

        args = {"paths": paths}
        try:
            result = self._call_mcp_tool("read_multiple_files", args)
            try:
                logger.debug("Response body:")
                logger.debug(
                    json.dumps(
                        getattr(result, "body", result), ensure_ascii=False, indent=2
                    )
                )
            except Exception:
                logger.debug(f"Response: {result}")

            if result.success:
                files_content = parse_multiple_files_response(result.data)
                return MultipleFileContentResult(
                    request_id=result.request_id,
                    success=True,
                    contents=files_content,
                )
            else:
                return MultipleFileContentResult(
                    request_id=result.request_id,
                    success=False,
                    error_message=result.error_message
                    or "Failed to read multiple files",
                )
        except Exception as e:
            return MultipleFileContentResult(
                request_id="",
                success=False,
                error_message=f"Failed to read multiple files: {e}",
            )

    def search_files(
        self,
        path: str,
        pattern: str,
        exclude_patterns: Optional[List[str]] = None,
    ) -> FileSearchResult:
        """
        Search for files in the specified path using a pattern.

        Args:
            path: The base directory path to search in.
            pattern: The glob pattern to search for.
            exclude_patterns: Optional list of patterns to exclude from the search.

        Returns:
            FileSearchResult: Result object containing matching file paths and error
                message if any.
        """

        args: Dict[str, Any] = {"path": path, "pattern": pattern}
        if exclude_patterns:
            args["excludePatterns"] = exclude_patterns

        try:
            result = self._call_mcp_tool("search_files", args)
            logger.debug(f"Response from CallMcpTool - search_files: {result}")

            if result.success:
                # Handle "No matches found" case
                if (
                    result.data
                    and result.data.strip()
                    and result.data.strip() != "No matches found"
                ):
                    matching_files = result.data.strip().split("\n")
                else:
                    matching_files = []
                return FileSearchResult(
                    request_id=result.request_id,
                    success=True,
                    matches=matching_files,
                )
            else:
                return FileSearchResult(
                    request_id=result.request_id,
                    success=False,
                    error_message=result.error_message or "Failed to search files",
                )
        except Exception as e:
            return FileSearchResult(
                request_id="",
                success=False,
                error_message=f"Failed to search files: {e}",
            )

    def _get_file_change(self, path: str) -> FileChangeResult:
        """
        Get file change information for the specified directory path.

        Args:
            path: The directory path to monitor for file changes.

        Returns:
            FileChangeResult: Result object containing parsed file change events and
                error message if any.
        """

        def parse_file_change_data(raw_data: str) -> List[FileChangeEvent]:
            """
            Parse the raw file change data into FileChangeEvent objects.

            Args:
                raw_data (str): Raw JSON string containing file change events.

            Returns:
                List[FileChangeEvent]: List of parsed file change events.
            """
            events = []
            try:
                # Parse the JSON array
                change_data = json.loads(raw_data)
                if isinstance(change_data, list):
                    for event_dict in change_data:
                        if isinstance(event_dict, dict):
                            event = FileChangeEvent.from_dict(event_dict)
                            events.append(event)
                else:
                    logger.warning(f"Expected list but got {type(change_data)}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON data: {e}")
                logger.warning(f"Raw data: {raw_data}")
            except Exception as e:
                logger.warning(f"Unexpected error parsing file change data: {e}")

            return events

        args = {"path": path}
        try:
            result = self._call_mcp_tool("get_file_change", args)
            try:
                logger.debug("Response body:")
                logger.debug(
                    json.dumps(
                        getattr(result, "body", result), ensure_ascii=False, indent=2
                    )
                )
            except Exception:
                logger.debug(f"Response: {result}")

            if result.success:
                # Parse the file change events
                events = parse_file_change_data(result.data)
                return FileChangeResult(
                    request_id=result.request_id,
                    success=True,
                    events=events,
                    raw_data=result.data,
                )
            else:
                return FileChangeResult(
                    request_id=result.request_id,
                    success=False,
                    raw_data=getattr(result, "data", ""),
                    error_message=result.error_message or "Failed to get file change",
                )
        except Exception as e:
            return FileChangeResult(
                request_id="",
                success=False,
                error_message=f"Failed to get file change: {e}",
            )

    def watch_directory(
        self,
        path: str,
        callback: Callable[[List[FileChangeEvent]], None],
        interval: float = 1.0,
        stop_event: Optional[threading.Event] = None,
    ) -> threading.Thread:
        """
        Watch a directory for file changes and call the callback function when changes occur.

        Args:
            path: The directory path to monitor for file changes.
            callback: Callback function that will be called with a list of FileChangeEvent
                objects when changes are detected.
            interval: Polling interval in seconds. Defaults to 1.0.
            stop_event: Optional threading.Event to stop the monitoring. If not provided,
                a new Event will be created and returned via the thread object.

        Returns:
            threading.Thread: The monitoring thread. Call thread.start() to begin monitoring.
                Use the thread's stop_event attribute to stop monitoring.
        """

        def _monitor_directory():
            """Internal function to monitor directory changes."""
            logger.info(f"Starting directory monitoring for: {path}")
            logger.info(f"Polling interval: {interval} seconds")

            while not stop_event.is_set():
                try:
                    # Get current file changes
                    result = self._get_file_change(path)

                    if result.success:
                        current_events = result.events

                        # Always call callback with current events (no deduplication)
                        logger.debug(f"Detected {len(current_events)} file changes:")
                        for event in current_events:
                            logger.debug(f"  - {event}")

                        try:
                            callback(current_events)
                        except Exception as e:
                            logger.error(f"Error in callback function: {e}")

                    else:
                        logger.error(f"Error monitoring directory: {result.error_message}")

                    # Wait for the next poll
                    stop_event.wait(interval)

                except Exception as e:
                    logger.error(f"Unexpected error in directory monitoring: {e}")
                    stop_event.wait(interval)

            logger.info(f"Stopped monitoring directory: {path}")

        # Create stop event if not provided
        if stop_event is None:
            stop_event = threading.Event()

        # Create and configure the monitoring thread
        monitor_thread = threading.Thread(
            target=_monitor_directory,
            name=f"DirectoryWatcher-{path.replace('/', '_')}",
            daemon=True,
        )

        # Add stop_event as an attribute to the thread for easy access
        setattr(monitor_thread, "stop_event", stop_event)
        return monitor_thread
