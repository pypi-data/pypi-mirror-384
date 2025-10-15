import os

def save_to_file(file_path, data):
    """Save data to a file."""
    with open(file_path, 'w') as file:
        file.write(data)


def load_from_file(file_path):
    """Load data from a file."""
    with open(file_path, 'r') as file:
        return file.read()


def ensure_dir(directory):
    """Ensure that a directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)