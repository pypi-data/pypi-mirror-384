import os


def _get_folder() -> str:
    folder = os.getenv('DISTRIBUTION_DATA_FOLDER', './data')
    os.makedirs(folder, exist_ok=True)
    return folder


def _load_from_folder(folder: str, key: str):
    try:
        with open(os.path.join(folder, key), 'rb') as f:
            return f.read()
    except Exception:
        # in case the file does not exist, should simply return None
        return None


def _write_to_folder(folder, filepath, content):
    path = os.path.join(folder, filepath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(content)
