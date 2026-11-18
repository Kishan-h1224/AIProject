
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.tools.registry import register_tool


# ---------------------------------
# 1. Directory configuration
# ---------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"

MAX_FILE_SIZE = 100_000
MAX_CONTENT_SIZE = 50_000

ALLOWED_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".json",
    ".csv"
}


# ---------------------------------
# 2. Argument validation
# ---------------------------------

class FileToolArgs(BaseModel):

    model_config = ConfigDict(
        strict=True,
        extra="forbid"
    )

    operation: Literal["read", "write", "append"]

    filename: str = Field(
        min_length=1,
        max_length=200
    )

    content: str | None = Field(
        default=None,
        max_length=MAX_CONTENT_SIZE
    )


# ---------------------------------
# 3. Path security
# ---------------------------------

def verify_safe_path(path: Path) -> Path:

    root = DATA_DIR.resolve()
    resolved = path.resolve(strict=False)

    try:
        resolved.relative_to(root)

    except ValueError:
        raise PermissionError(
            "Access outside data directory denied"
        )

    # Reject symbolic links in existing components.
    current = DATA_DIR

    relative = resolved.relative_to(root)

    for part in relative.parts:
        current = current / part

        if current.is_symlink():
            raise PermissionError(
                "Symbolic links are not allowed"
            )

    return resolved


def get_safe_path(filename: str) -> Path:

    relative_path = Path(filename)

    if not filename.strip():
        raise ValueError("Filename cannot be empty")

    if relative_path.is_absolute() or relative_path.drive:
        raise PermissionError(
            "Absolute paths are not allowed"
        )

    if ".." in relative_path.parts:
        raise PermissionError(
            "Path traversal is not allowed"
        )

    if not relative_path.name:
        raise ValueError("Invalid filename")

    if relative_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise PermissionError(
            "File extension is not allowed"
        )

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    safe_path = verify_safe_path(DATA_DIR / relative_path)

    # Recheck existing parent directories.
    parent = safe_path.parent

    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)

    verify_safe_path(safe_path)

    return safe_path


# ---------------------------------
# 4. File I/O tool
# ---------------------------------

@register_tool(
    "file_io",
    FileToolArgs,
    requires_approval=lambda args: args["operation"] in {"write", "append"}
)
def file_io(
    operation: Literal["read", "write", "append"],
    filename: str,
    content: str | None = None
) -> dict:

    path = get_safe_path(filename)

    # Revalidate immediately before file access.
    verify_safe_path(path)

    if operation == "read":

        if not path.is_file():
            raise FileNotFoundError(
                "File does not exist"
            )

        if path.stat().st_size > MAX_FILE_SIZE:
            raise ValueError(
                "File size exceeds allowed limit"
            )

        verify_safe_path(path)

        with path.open("rb") as file:
            data = file.read(MAX_FILE_SIZE + 1)

        if len(data) > MAX_FILE_SIZE:
            raise ValueError(
                "File size exceeds allowed limit"
            )

        return {
            "status": "success",
            "filename": filename,
            "content": data.decode(
                "utf-8",
                errors="strict"
            )
        }

    if content is None:
        raise ValueError(
            "Content is required for write and append"
        )

    encoded_content = content.encode("utf-8")

    if len(encoded_content) > MAX_CONTENT_SIZE:
        raise ValueError(
            "Content exceeds allowed size"
        )

    if operation == "append":

        if not path.is_file():
            raise FileNotFoundError(
                "Cannot append: file does not exist"
            )

        if path.stat().st_size > MAX_FILE_SIZE:
            raise ValueError(
                "Existing file exceeds allowed limit"
            )

        current_size = path.stat().st_size

    else:
        current_size = 0

    if current_size + len(encoded_content) > MAX_FILE_SIZE:
        raise ValueError(
            "Resulting file would exceed allowed size"
        )

    # Create parent directories if required.
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    verify_safe_path(path)

    if operation == "write":

        # Exclusive creation: existing files are not overwritten.
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL

    else:

        flags = os.O_WRONLY | os.O_APPEND

    # O_NOFOLLOW is available on some systems, but not Windows.
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    try:

        fd = os.open(
            str(path),
            flags,
            0o600
        )

        with os.fdopen(fd, "wb" if operation == "write" else "ab") as file:

            file.write(encoded_content)

    except FileExistsError:
        raise FileExistsError(
            "File already exists. Choose another filename."
        )

    return {
        "status": "success",
        "filename": filename,
        "operation": operation
    }


# ---------------------------------
# 5. Test File I/O
# ---------------------------------

if __name__ == "__main__":

    print("\nWriting file:")

    print(
        file_io(
            operation="write",
            filename="notes.txt",
            content="AutoAgent project started."
        )
    )

    print("\nReading file:")

    print(
        file_io(
            operation="read",
            filename="notes.txt"
        )
    )

    print("\nAppending content:")

    print(
        file_io(
            operation="append",
            filename="notes.txt",
            content="\nFile I/O tool implemented."
        )
    )

    print("\nReading updated file:")

    print(
        file_io(
            operation="read",
            filename="notes.txt"
        )
    )
