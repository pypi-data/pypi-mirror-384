from abc import abstractmethod

from ..utils.utils import Parsable, last_parameter, parameter


################################################################
class Downloader(Parsable):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    @abstractmethod
    def download(self) -> None:
        pass

    @last_parameter
    def destination() -> str:
        "Path to the destination folder. If not specified, defaults to the study numeric ID."
        pass

    @parameter
    def url() -> str:
        "URL or DOI of the study to download"
        pass


################################################################
