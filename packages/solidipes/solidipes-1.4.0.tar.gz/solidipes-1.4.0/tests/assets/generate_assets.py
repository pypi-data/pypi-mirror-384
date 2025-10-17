import pandas as pd
from PIL import Image


def main() -> None:
    generate_binary_assets()
    generate_text_assets()
    generate_table_assets()


def generate_binary_assets() -> None:
    generate_binary_file()
    generate_image_without_extension()


def generate_binary_file() -> None:
    """Generate a binary file with zeros."""
    file_size = 100
    with open("binary.bin", "wb") as f:
        f.write(b"\0" * file_size)


def generate_image_without_extension() -> None:
    """Generate a blank image of 1x1 pixels and export it in jpg."""
    image = Image.new("RGB", (1, 1))
    image.save("image", "JPEG")


def generate_text_assets() -> None:
    text = "Hello World!\n"
    with open("text.txt", "w") as f:
        f.write(text)


def generate_table_assets() -> None:
    df = pd.DataFrame({
        "a": [1, 4],
        "b": [2, 5],
        "c": [3, 6],
    })
    df.to_csv("table.csv", index=False)
    df.to_excel("table.xlsx", index=False)
