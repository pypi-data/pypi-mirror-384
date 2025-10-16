from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from stxsdk.storage.singleton import SingletonMeta


@dataclass
class User(metaclass=SingletonMeta):
    id: Optional[str] = None  # pylint: disable=C0103
    uid: Optional[str] = None
    session_id: Optional[str] = None
    token: Optional[str] = None
    refresh_token: Optional[str] = None
    expiry: Optional[datetime] = None
    email: Optional[str] = None

    def set_params(self, attributes: Dict[str, Any]) -> None:
        """
        It takes a dictionary of attribute names with their values, and sets the attributes
        of the object with new provided values
        :parameter attributes: A dictionary of attributes to set on the object
        :returns None
        """
        self.__dict__.update(attributes)

    def clear(self):
        self.__dict__.clear()
