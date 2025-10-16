import hashlib
from pathlib import Path


class MD5:
    """
    MD5: Class for hashing objects using the MD5 algorithm.
    """

    def __init__(self, obj: object, length: int = 8):
        self.obj = obj
        self.length = length

    @property
    def obj(self) -> bytes:
        # Get the object stored as bytes.
        return self._obj

    @obj.setter
    def obj(self, obj: object):
        # Set the object property.
        if isinstance(obj, (str, Path)) and Path(obj).is_file():
            with open(obj, "rb") as obj_file:
                self._obj = obj_file.read()
        else:
            self._obj = str(obj).encode()

    @property
    def hash(self) -> str:
        return hashlib.md5(self.obj).hexdigest()[: self.length]  # nosec
