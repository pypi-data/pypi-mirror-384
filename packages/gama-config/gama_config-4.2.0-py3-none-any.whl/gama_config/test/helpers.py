from pathlib import Path


def write_temp_file(content: str) -> Path:
    """
    Write a temporary file with the given content and return the path to it.
    """
    import tempfile

    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(content.encode())
    temp.close()
    return Path(temp.name)
