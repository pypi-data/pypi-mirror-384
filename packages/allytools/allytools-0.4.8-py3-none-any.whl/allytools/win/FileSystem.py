from pathlib import Path

def ensure_folder(path_str: str) -> bool:
    p = Path(path_str)
    if p.exists():
        if not p.is_dir():
            raise ValueError(f"Expected a directory path, got a file path: {path_str}")
    else:
        p.mkdir(parents=True)
    return True


def require_paths(*paths: Path) -> None:
    missing_dirs = [p for p in paths if p.suffix == "" and not p.is_dir()]
    missing_files = [p for p in paths if p.suffix != "" and not p.is_file()]

    if missing_dirs or missing_files:
        msg = []
        if missing_dirs:
            msg.append("Missing directories:\n  - " + "\n  - ".join(map(str, missing_dirs)))
        if missing_files:
            msg.append("Missing files:\n  - " + "\n  - ".join(map(str, missing_files)))
        raise FileNotFoundError("\n".join(msg))
