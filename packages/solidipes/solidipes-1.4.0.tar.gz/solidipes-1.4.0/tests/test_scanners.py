import os
from pathlib import Path

import solidipes as sp
from solidipes.loaders.file_sequence import FileSequence
from solidipes.scanners.scanner_local import ScannerLocal as Scanner

# Imported fixtures:
# - study_tree


def check_dict_same_structure(d1, d2) -> None:
    """Check if two dictionaries have the same structure.
    If values are primitive types, check if they are equal.
    Else, if values are class instances, just check the class.
    """
    assert d1.keys() == d2.keys()

    for k in d1.keys():
        v1 = d1[k]
        v2 = d2[k]

        if isinstance(v1, dict):
            check_dict_same_structure(v1, v2)

        elif type(v1) in [int, float, str, bool, list]:
            assert v1 == v2

        else:
            assert (type(v1) is type(v2)) or (type(v1) is v2) or (v1 is type(v2))


def test_get_loader_tree(study_tree: Path) -> None:
    """Test the Scanner.get_loader_tree method."""
    scanner = Scanner(search_path="data")
    tree = scanner.get_loader_tree()

    # Check tree structure
    expected_tree = {
        "subdir1": {
            "file*.txt": FileSequence,
            "other.txt": sp.loader.Text,
        },
        "subdir2": {
            "subdir3": {
                "file5.txt": sp.loader.Text,
            },
            "file6.txt": sp.loader.Text,
        },
        "file7.txt": sp.loader.Text,
    }

    check_dict_same_structure(tree, expected_tree)


class TestGetFilteredLoaderTree:
    def test_single_root(self, study_tree: Path) -> None:
        """Test the Scanner.get_filtered_loader_tree method on a tree with a single root."""
        scanner = Scanner()
        tree1 = scanner.get_filtered_loader_tree(["data"])
        tree2 = scanner.get_filtered_loader_tree(["data", os.path.join("data", "subdir1")])
        tree3 = scanner.get_filtered_loader_tree([
            os.path.join("data", "subdir1"),
            os.path.join("data", "subdir2"),
        ])

        # Check tree structure
        expected_tree = {
            "data": {
                "subdir1": {
                    "file*.txt": FileSequence,
                    "other.txt": sp.loader.Text,
                },
                "subdir2": {
                    "subdir3": {
                        "file5.txt": sp.loader.Text,
                    },
                    "file6.txt": sp.loader.Text,
                },
                "file7.txt": sp.loader.Text,
            }
        }

        check_dict_same_structure(tree1, expected_tree)

        # Check that data/subdir1 is not repeated in the second tree
        check_dict_same_structure(tree1, tree2)

        # Check that the root is still "data" in the third tree
        assert list(tree3.keys()) == ["data"]

    def test_multiple_roots(self, study_tree: Path) -> None:
        """Test the Scanner.get_filtered_loader_tree method on a tree with multiple roots."""
        os.chdir(study_tree / "data")
        scanner = Scanner()
        tree = scanner.get_filtered_loader_tree(["subdir1", "subdir2"])

        from pprint import pprint

        pprint(tree)

        # Check tree structure
        expected_tree = {
            "subdir1": {
                "file*.txt": FileSequence,
                "other.txt": sp.loader.Text,
            },
            "subdir2": {
                "subdir3": {
                    "file5.txt": sp.loader.Text,
                },
                "file6.txt": sp.loader.Text,
            },
        }

        check_dict_same_structure(tree, expected_tree)


def test_is_excluded(study_tree: Path) -> None:
    """Test the Scanner.is_excluded method."""
    scanner = Scanner(reload_excluded=False)
    scanner.excluded_patterns = ["other*", "subdir3/"]

    # Test method
    assert scanner.is_excluded("other.txt")
    assert scanner.is_excluded(os.path.join("data", "subdir1", "other.txt"))
    assert scanner.is_excluded(os.path.join("data", "subdir2", "subdir3"))

    # Test scanning
    tree = scanner.get_filtered_loader_tree(["data"])

    expected_tree = {
        "data": {
            "subdir1": {
                "file*.txt": FileSequence,
            },
            "subdir2": {
                "file6.txt": sp.loader.Text,
            },
            "file7.txt": sp.loader.Text,
        }
    }

    check_dict_same_structure(tree, expected_tree)


# def test_list_files(study_tree: Path) -> None:
#     """Test the list_files function."""

#     scanner = scanner_module.Scanner()
#     tree = scanner.get_filtered_loader_tree(["data"])
#     files = scanner_module.list_files(tree)  # list of tuples (file_path, value)

#     file_paths = [f[0] for f in files]
#     values = [f[1] for f in files]  # dict or File

#     expected_file_paths = [
#         "data",
#         "data/subdir1",
#         "data/subdir1/other.txt",
#         "data/subdir1/file*.txt",
#         "data/subdir2",
#         "data/subdir2/subdir3",
#         "data/subdir2/subdir3/file5.txt",
#         "data/subdir2/file6.txt",
#         "data/file7.txt",
#     ]

#     assert file_paths == expected_file_paths

#     check_dict_same_structure(values[0], tree["data"])
#     check_dict_same_structure(values[1], tree["data"]["subdir1"])
#     assert type(values[2]) is sp.loader.Text
