from datetime import datetime


class ResourceFile:
    def __init__(self, 
                 name: str, 
                 version: int, 
                 filename: str,
                 resource_type: str,
                 description: str | None = None,
                 created_at: datetime | None = None):
        self._name = name
        self._version = version
        self._filename = filename
        self._resource_type = resource_type
        self._description = description
        self._created_at = created_at

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def version(self) -> int:
        return self._version
    
    @property
    def filename(self) -> str:
        return self._filename
    
    @property
    def resource_type(self) -> str:
        return self._resource_type

    @property
    def created_at(self) -> datetime | None:
        return self._created_at

    @property
    def description(self) -> str | None:
        return self._description
