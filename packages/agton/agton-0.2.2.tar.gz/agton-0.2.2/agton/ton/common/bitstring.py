from bitarray import frozenbitarray
from bitarray.util import int2ba, ba2int

BitString = frozenbitarray

def int2bs(v: int, len: int) -> BitString:
    return BitString(int2ba(v, len))

def bs2int(bs: BitString, signed: bool = True) -> int:
    return ba2int(bs, signed=signed)