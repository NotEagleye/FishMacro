from pathlib import Path

import json

BASE_DIR = Path(__file__).resolve().parent

ASSETS_DIR = BASE_DIR / "Assets"
DATA_DIR = BASE_DIR / "Data"

def Decode_JSON(Path):
    if not Path.exists():
        print(f"Error: file not found at {Path}")
        return None

    try:
        with open(Path, 'r') as f:
            Data = json.load(f)
            return Data
    except json.JSONDecodeError as Error:
        print(f"Error decoding JSON in file: {Error}")
        return None

