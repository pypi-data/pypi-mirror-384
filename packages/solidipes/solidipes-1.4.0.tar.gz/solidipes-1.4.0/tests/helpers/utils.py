import os

from PIL import Image
from pixelmatch.contrib.PIL import pixelmatch

# Path from /tests directory
assets_path_list = ["assets"]
tmp_path_list = ["tmp"]


def get_asset_path(filename):
    """Return the absolute path to an asset file."""
    return get_absolute_path(assets_path_list + [filename])


def get_tmp_path(filename):
    """Return the absolute path to a temporary file."""
    return get_absolute_path(tmp_path_list + [filename])


def get_absolute_path(path_list):
    """Return the absolute path to a file."""
    tests_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(tests_path, "..", *path_list)
    return file_path


def image_similarity(image1_path, image2_path, threshold=4000):
    # Convert image bytes to PIL Images
    img1 = Image.open(image1_path)
    img2 = Image.open(image2_path)

    # Ensure images are the same size
    img1 = img1.resize(img2.size)
    diff = Image.new("RGB", img2.size)
    nbr_different = pixelmatch(img1, img2, diff, threshold=0.31)
    return nbr_different <= threshold


def remove_if_empty(directory) -> None:
    if not os.path.exists(directory):
        return

    if not os.listdir(directory):
        try:
            os.rmdir(directory)
        except OSError as e:
            print(f"Error removing directory {directory}: {e}")
