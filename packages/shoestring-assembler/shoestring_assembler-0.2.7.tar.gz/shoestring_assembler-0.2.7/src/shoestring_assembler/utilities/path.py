from pathlib import Path

def as_string(path:Path):
    if path.is_absolute():
        return f"{path}"
    else:
        return f"./{path}"