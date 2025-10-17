"""Prompt building utilities for Pydantic AI agent, including file handling and context management."""

import mimetypes
from pathlib import Path

from pydantic_ai import BinaryContent

from aixtools.context import SessionIdTuple
from aixtools.server import container_to_host_path
from aixtools.utils.files import is_text_content

CLAUDE_MAX_FILE_SIZE_IN_CONTEXT = 4 * 1024 * 1024  # Claude limit 4.5 MB for PDF files
CLAUDE_IMAGE_MAX_FILE_SIZE_IN_CONTEXT = (
    5 * 1024 * 1024
)  # Claude limit 5 MB for images, to avoid large image files in context


def should_be_included_into_context(
    file_content: BinaryContent | str | None,
    file_size: int,
    *,
    max_img_size_bytes: int = CLAUDE_IMAGE_MAX_FILE_SIZE_IN_CONTEXT,
    max_file_size_bytes: int = CLAUDE_MAX_FILE_SIZE_IN_CONTEXT,
) -> bool:
    """Decide whether a file content should be included into the model context based on its type and size."""
    if not isinstance(file_content, BinaryContent):
        return False

    if file_content.media_type.startswith("text/"):
        return False

    # Exclude archive files as they're not supported by OpenAI models
    archive_types = {
        "application/zip",
        "application/x-tar",
        "application/gzip",
        "application/x-gzip",
        "application/x-rar-compressed",
        "application/x-7z-compressed",
    }
    if file_content.media_type in archive_types:
        return False

    if file_content.is_image and file_size < max_img_size_bytes:
        return True

    return file_size < max_file_size_bytes


def file_to_binary_content(file_path: str | Path, mime_type: str = "") -> str | BinaryContent:
    """
    Read a file and return its content as either a UTF-8 string (for text files)
    or BinaryContent (for binary files).
    """
    with open(file_path, "rb") as f:
        data = f.read()

    if not mime_type:
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or "application/octet-stream"

    if is_text_content(data, mime_type):
        return data.decode("utf-8")

    return BinaryContent(data=data, media_type=mime_type)


def build_user_input(
    session_tuple: SessionIdTuple,
    user_text: str,
    file_paths: list[Path],
) -> str | list[str | BinaryContent]:
    """Build user input for the Pydantic AI agent, including file attachments if provided."""
    if not file_paths:
        return user_text

    attachment_info_lines = []
    binary_attachments = []

    for workspace_path in file_paths:
        host_path = container_to_host_path(workspace_path, ctx=session_tuple)
        file_size = host_path.stat().st_size
        mime_type, _ = mimetypes.guess_type(host_path)
        mime_type = mime_type or "application/octet-stream"

        attachment_info = f"* {workspace_path.name} (file_size={file_size} bytes) (path in workspace: {workspace_path})"
        binary_content = file_to_binary_content(host_path, mime_type)

        if should_be_included_into_context(binary_content, file_size):
            binary_attachments.append(binary_content)
            attachment_info += f" -- provided to model context at index {len(binary_attachments) - 1}"

        attachment_info_lines.append(attachment_info)

    full_prompt = user_text + "\nAttachments:\n" + "\n".join(attachment_info_lines)

    return [full_prompt] + binary_attachments
