from typing import Iterable

class BytesParser:
    def __init__(self, b: bytes):
        self.b = b
        self.i = 0
    
    def preload_bytes(self, n: int) -> bytes:
        return self.b[self.i:self.i + n]
    
    def load_bytes(self, n: int) -> bytes:
        self.i += n
        return self.b[self.i - n:self.i]
    
    def skip_bytes(self, n: int):
        self.i += n

    def expect(self, v: int | Iterable[int] | bytes):
        if isinstance(v, int):
            v = [v]
        if not isinstance(v, bytes):
            v = bytes(v)
        n = len(v)
        b = self.preload_bytes(n)
        if b != v:
            raise ValueError('Expected {v}, but {b} found')
        self.i += n
    
    def load_uint(self, byte_size: int) -> int:
        b = self.load_bytes(byte_size)
        return int.from_bytes(b, 'big')
    
    def end_parse(self):
        if self.i != len(self.b):
            raise ValueError('Expected end of bytes')
