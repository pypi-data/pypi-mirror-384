import uuid
from typing import Optional


class NodeUUID:
    def __init__(self, initial_uuid: Optional[str] = None):
        self._uuid = initial_uuid if initial_uuid else self._generate_uuid4()

    @staticmethod
    def _generate_uuid4() -> str:
        _uuid = str(uuid.uuid4())
        return _uuid

    def update_uuid(self) -> str:
        _uuid = self._generate_uuid4()
        self.uuid = _uuid
        return _uuid

    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(
        self,
        new_uuid: str,
    ):
        if new_uuid and isinstance(new_uuid, str):
            self._uuid = new_uuid
        else:
            raise ValueError("UUID should exist and be type str")
