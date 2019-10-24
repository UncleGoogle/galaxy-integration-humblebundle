import abc
from typing import Optional


class DownloadStruct(abc.ABC):
    """
    url: Dict[str, str]         # {'bittorent': str, 'web': str}
    file_size: str
    md5: str
    name: str: Optional[str]  # asmjs downloads have no 'name'
    uploaded_at: Optional[str]  # ex.: 2019-07-10T21:48:11.976780
    """
    def __init__(self, data: dict):
        self._data = data
        self.url = data.get('url')
    
    def __str__(self):
        return f"<{self.__class__.__name__}> '{self.name}'"

    def __repr__(self):
        return f"{self}: {self._data}"

    @property
    def name(self) -> Optional[str]:
        return self._data.get('name')

    @property
    def web(self) -> Optional[str]:
        if self.url is None:
            return None
        return self.url['web']

    @property
    def bittorrent(self) -> Optional[str]:
        if self.url is None:
            return None
        return self.url.get('bittorrent')

    @abc.abstractmethod
    def human_size(self) -> str:
        pass


class TroveDownload(DownloadStruct):
    """ Additional fields:
    sha1: str
    timestamp: int          # ?
    machine_name: str
    size: str
    """
    @property
    def human_size(self):
        return self._data['size']

    @property
    def machine_name(self):
        return self._data['machine_name']


class SubproductDownload(DownloadStruct):
    """ Additional fields:
    human_size: str
    """
    @property
    def human_size(self):
        return self._data['human_size']
