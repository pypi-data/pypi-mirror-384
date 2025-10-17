import monocypher
from typing import Union
from hashlib import md5
class ChaCha20():
    def __init__(self, key: Union[bytes, str]) -> None:
        if isinstance(key, str):
            key = key.encode()
        m = md5()
        m.update(key)
        self.key = m.hexdigest().encode()
        self.nonce = self.key[:24]

    def __call__(self, data: bytes) -> bytearray:
        return monocypher.chacha20(self.key, self.nonce, data)

