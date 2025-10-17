from pathlib import Path

def is_binary_file(file_path: Path) -> bool:
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(512)
            return b'\0' in chunk
    except:
        return True

def get_file_size_mb(file_path: Path) -> float:
    try:
        return file_path.stat().st_size / (1024 * 1024)
    except:
        return 0
