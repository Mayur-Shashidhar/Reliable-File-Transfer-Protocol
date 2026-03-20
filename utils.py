import os

def split_file(filepath, chunk_size):
    with open(filepath, 'rb') as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data


def get_file_size(filepath):
    return os.path.getsize(filepath)