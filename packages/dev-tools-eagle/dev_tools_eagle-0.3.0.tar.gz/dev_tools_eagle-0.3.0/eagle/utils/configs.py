# -*- coding: utf-8 -*-
from pathlib import Path
from dotenv import load_dotenv

def find_env_upwards(filename: str = ".env", start_path: Path = None) -> Path | None:
    if start_path is None:
        start_path = Path.cwd()
    for parent in [start_path, *start_path.parents]:
        candidate = parent / filename
        if candidate.exists():
            load_dotenv(candidate)
            return True
    raise FileNotFoundError(f"Could not find {filename} in {start_path} or its parents.")
