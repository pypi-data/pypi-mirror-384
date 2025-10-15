from typing import Optional, TYPE_CHECKING
from emdb.models.entry import EMDBEntry

if TYPE_CHECKING:
    from emdb.client import EMDB


class LazyEMDBEntry:
    def __init__(self, emdb_id: str, client: "EMDB"):
        self._id = emdb_id
        self._client = client
        self._entry: Optional[EMDBEntry] = None

    def _load(self):
        if self._entry is None:
            self._entry = self._client.get_entry(self._id)

    def __getattr__(self, name):
        self._load()
        return getattr(self._entry, name)

    def __str__(self):
        return f"<LazyEMDBEntry {self._id}>"

    def __repr__(self):
        return self.__str__()
