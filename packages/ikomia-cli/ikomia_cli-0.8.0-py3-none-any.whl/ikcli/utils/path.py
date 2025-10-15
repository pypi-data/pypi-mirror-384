"""Some utils about path management."""

from pathlib import Path

from yarl import URL


def from_uri(url: URL) -> Path:
    """
    Convert a yarl URL to Path.

    When python>3.13, use Path.from_uri() instead of this.

    Args:
        url: An url to convert to path

    Returns:
        A path from URL

    Raises:
        ValueError: when url is not well formed
    """
    # Greatly inspired from future Path.from_uri function

    # Sanity check
    if url.scheme != "file":
        raise ValueError(f"URL sheme is not 'file' ! {url}")

    # Extract path
    path = url.path

    # Windows stuff replacement
    if path[:3] == "///" or (path[:1] == "/" and path[2:3] in ":|"):
        # Remove slash before DOS device/UNC path
        path = path[1:]
    if path[1:2] == "|":
        # Replace bar with colon in DOS drive
        path = path[:1] + ":" + path[2:]

    # Now it's ready to convert to Path
    p = Path(path)

    # Sanity check, ensure is absolute
    if not p.is_absolute():
        raise ValueError(f"URL is not absolute: {url}")
    return p
