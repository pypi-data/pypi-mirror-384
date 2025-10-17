from pathlib import Path

import solidipes as sp


class TestLoaders:
    def test_file_valid(self, study_dir: Path) -> None:
        # Create file
        file_path = study_dir / "file.txt"
        with file_path.open("w") as f:
            f.write("Hello World!")

        # Load file
        file = sp.loader.Text(path=str(file_path))

        # Check valid loading
        assert file.is_valid

    def test_file_empty(self, study_dir: Path) -> None:
        # Create file
        file_path = study_dir / "file.txt"

        with file_path.open("w"):
            pass

        # Load file
        file = sp.loader.Text(path=str(file_path))

        # Check valid loading
        assert not file.is_valid

    def test_file_invalid_extension(self, study_dir: Path) -> None:
        # Create file
        file_path = study_dir / "file.dat"

        with file_path.open("w") as f:
            f.write("Hello World!")

        # Load file
        file = sp.loader.Text(path=str(file_path))

        # Check valid loading
        assert len(file.errors) > 0
        assert not file.is_valid

    def test_file_invalid_mime(self, study_dir: Path) -> None:
        # Create file
        file_path = study_dir / "file.jpg"

        with file_path.open("w") as f:
            f.write("Hello World!")

        # Load file
        file = sp.loader.Image(path=str(file_path))

        # Check valid loading
        assert not file.is_valid

    def test_file_wrong_loader(self, study_dir: Path) -> None:
        # Create file
        file_path = study_dir / "file.txt"

        with file_path.open("w") as f:
            f.write("Hello World!")

        # Load file
        file = sp.loader.Image(path=str(file_path))

        # Check valid loading
        assert not file.is_valid

    def test_code_snippet_valid(self, study_dir: Path) -> None:
        # Create file
        file_path = study_dir / "file.py"

        with file_path.open("w") as f:
            f.write("print('Hello World!')")

        # Load file
        file = sp.loader.CodeSnippet(path=str(file_path))

        # Check valid loading
        assert file.is_valid

    def test_code_snippet_invalid_lint(self, study_dir: Path) -> None:
        # Create file
        file_path = study_dir / "file.py"

        with file_path.open("w") as f:
            f.write("print('Hello World'")

        # Load file
        file = sp.loader.CodeSnippet(path=str(file_path))

        # Check valid loading
        assert not file.is_valid

    def test_binary(self, study_dir: Path) -> None:
        # Create file
        file_path = study_dir / "file.bin"

        with file_path.open("wb") as f:
            f.write(b"\x00\x01\x02\x03")

        # Load file
        file = sp.loader.Binary(path=str(file_path))

        # Check valid loading
        assert not file.is_valid

    def test_disabling_validator(self, study_dir: Path) -> None:
        # Create file
        file_path = study_dir / "file.bin"

        with file_path.open("wb") as f:
            f.write(b"\x00\x01\x02\x03")

        # Load file
        file = sp.loader.Binary(path=str(file_path))

        # Check valid loading
        assert not file.is_valid

        # Disable validator
        file.disable_validator("HasValidExtensionValidator")
        assert file.is_valid

    def test_validator_cache(self, study_dir: Path) -> None:
        # Create file
        file_path = study_dir / "file.bin"

        with file_path.open("wb") as f:
            f.write(b"\x00\x01\x02\x03")

        # Load file
        file = sp.loader.Binary(path=str(file_path))

        # Check caching of disabled validator
        validator_name = "HasValidExtensionValidator"
        file.disable_validator(validator_name)
        assert not file.validator_enabled[validator_name]

        sp.close_cached_metadata()
        file = sp.loader.Binary(path=str(file_path))
        assert not file.validator_enabled[validator_name]

        # Check caching of enabled validator
        file.enable_validator(validator_name)
        assert file.validator_enabled[validator_name]

        sp.close_cached_metadata()
        file = sp.loader.Binary(path=str(file_path))
        assert file.validator_enabled[validator_name]
