import os
import subprocess
import tempfile
from pathlib import Path


def edit_text(initial_text: str, file_name: str) -> str:
    # Determine editor (Unix convention)
    editor = (
            os.environ.get("VISUAL")
            or os.environ.get("EDITOR")
            or ("notepad" if os.name == "nt" else "vi")
    )

    with tempfile.NamedTemporaryFile(
            mode="w+",
            suffix=file_name,
            delete=False,
            encoding="utf-8",
    ) as tmp:
        tmp.write(initial_text)
        tmp.flush()
        path = Path(tmp.name)

    try:
        # Launch editor and wait for it to close
        subprocess.run([editor, str(path)], check=True)

        # Read edited content
        return path.read_text(encoding="utf-8")

    finally:
        path.unlink(missing_ok=True)
