from typing import Iterable
import json
from pathlib import Path
from typing import Any


class Manifest:
    def __init__(self, data: dict[str, Any]):
        self.data = data

    @classmethod
    def from_path(cls, path: Path):
        with path.open() as fh:
            data = json.load(fh)
            return Manifest(data=data)
        
    def iter_models(self) -> Iterable[dict[str, Any]]:
        for node in self.data['nodes'].values():
            if node['resource_type'] == 'model':
                yield node
