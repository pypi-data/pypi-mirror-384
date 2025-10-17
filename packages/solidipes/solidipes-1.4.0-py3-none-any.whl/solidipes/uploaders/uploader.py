import argparse
from abc import abstractmethod
from typing import TYPE_CHECKING

from solidipes.utils.utils import classproperty, last_parameter_with_default

from ..utils.utils import Parsable

if TYPE_CHECKING:
    from solidipes_core_plugin.reports.widgets.uploader import UploaderWidget


################################################################
class Uploader(Parsable):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    @abstractmethod
    def upload(self, args: argparse.Namespace) -> None:
        pass

    @last_parameter_with_default
    def directory() -> str:
        """Path to the directory containing the study to upload. Defaults to the root of the current Solidipes
        study."""
        from ..utils.utils import get_study_root_path

        return get_study_root_path()

    @classproperty
    @abstractmethod
    def report_widget_class(self) -> "type[UploaderWidget] | None":
        """Return the corresponding streamlit widget for the uploader."""

        return None


################################################################
