from typing import Optional

from ..scanners.scanner import Scanner
from ..scanners.scanner_dtool import ScannerDTool
from ..scanners.scanner_local import ScannerLocal
from ..utils import solidipes_logging as logging
from ..utils.progress import ProgressBar, get_progress_bar
from ..utils.utils import get_path_relative_to_root
from .validator import Validator, add_validation_error

print = logging.invalidPrint
logger = logging.getLogger()


class CurationValidator(Validator):
    """Validator for curation."""

    def __init__(self, description: str = "All files are valid", **kwargs) -> None:
        super().__init__(description=description, **kwargs)
        self._scanner: Optional[Scanner] = None
        self._first_run = True
        self.remote = False

    @property
    def scanner(self) -> Scanner:
        if self._scanner is None:
            type_scanner = ScannerLocal
            if self.remote:
                type_scanner = ScannerDTool
            self._scanner = type_scanner()

        return self._scanner

    def _validate(self, obj=None) -> bool:
        loader_tree = self.scanner.get_loader_tree()
        errors = []
        progress = get_progress_bar("Validating files", total=loader_tree.count)

        with progress:

            def collect_errors(loader) -> None:
                path = get_path_relative_to_root(loader.path)
                if isinstance(progress, ProgressBar):
                    progress.update(advance=1, text=path)

                if loader.is_valid:
                    return

                error = f'"{path}" is not valid:'

                for validation_result in loader.validation_results:
                    if validation_result.valid or validation_result.validator.name == "OntologyIsMatchedValidator":
                        continue

                    for validation_error in validation_result.errors:
                        error += f"\n  - {validation_error}"

                errors.append(error)

            loader_tree.apply(collect_errors)

        for error in errors:
            add_validation_error(error)

        is_valid = len(errors) == 0
        self._first_run = False
        return is_valid
