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

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / file_name
        path.write_text(initial_text, encoding="utf-8")

        # Launch editor and wait for it to close
        subprocess.run([editor, str(path)], check=True)

        # Read edited content
        return path.read_text(encoding="utf-8")
