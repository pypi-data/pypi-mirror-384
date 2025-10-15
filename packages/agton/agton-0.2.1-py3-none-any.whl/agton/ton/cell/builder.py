from __future__ import annotations

from typing import Self, Iterable, overload, TYPE_CHECKING

from bitarray import bitarray, frozenbitarray
from bitarray.util import int2ba

from .cell import Cell
from .exceptions import CellOverflow

if TYPE_CHECKING:
    from ..types.tlb import TlbConstructor
    from ..types.msg_address import Address, MsgAddress, MsgAddressInt, MsgAddressExt
    from ..types.hashmap import HashmapE, Hashmap
    from .slice import Slice


MAX_BITS: int = 1023
MAX_REFS: int = 4

class Builder:
    def __init__(self) -> None:
        self.data = bitarray()
        self.refs = []
    
    @property
    def remaining_bits(self):
        return MAX_BITS - len(self.data)
    
    @property
    def remaining_refs(self):
        return MAX_REFS - len(self.refs)
    
    def end_cell(self) -> Cell:
        return Cell(frozenbitarray(self.data), self.refs)
    
    def to_cell(self) -> Cell:
        return self.end_cell()
    
    def to_slice(self) -> Slice:
        return self.to_cell().to_slice()
    
    def _ensure_bits_cap(self, n: int):
        if n > self.remaining_bits:
            raise CellOverflow(f"Can't store {n} more bits, only {self.remaining_bits} bits available")
    
    def _ensure_refs_cap(self, n: int):
        if n > self.remaining_refs:
            raise CellOverflow(f"Can't store {n} more refs, only {self.remaining_refs} refs available")
    
    def store_ref(self, c: Cell) -> Self:
        self._ensure_refs_cap(1)
        self.refs.append(c)
        return self
    
    def store_bit(self, b: int | bool | str) -> Self:
        if isinstance(b, str):
            if b not in ('0', '1'):
                raise ValueError("Expected only 0 and 1 as str argument")
            b = int(b)
        if isinstance(b, int):
            if b not in (0, 1):
                raise ValueError("Expected only 0 or 1 as int argument")
            b = bool(b)
        return self.store_bool(b)

    def store_bits(self, b: bitarray | str | Iterable[int]) -> Self:
        if not isinstance(b, bitarray):
            b = bitarray(b)
        self._ensure_bits_cap(len(b))
        self.data.extend(b)
        return self

    def store_bytes(self, b: bytes) -> Self:
        n = len(b) * 8
        self._ensure_bits_cap(n)
        self.data.frombytes(b)
        return self
    
    def store_uint(self, v: int, n: int) -> Self:
        b = int2ba(v, n, signed=False)
        self.store_bits(b)
        return self
    
    def store_int(self, v: int, n: int) -> Self:
        b = int2ba(v, n, signed=True)
        self.store_bits(b)
        return self
    
    def store_bool(self, b: bool) -> Self:
        return self.store_uint(b, 1)
    
    def store_var_uint(self, v: int, n: int):
        bit_length = (n - 1).bit_length()
        if v == 0:
            return self.store_uint(0, bit_length)
        byte_length = (v.bit_length() + 7) // 8
        return self.store_uint(byte_length, bit_length).store_uint(v, byte_length * 8)

    def store_var_int(self, v: int, n: int):
        bit_length = (n - 1).bit_length()
        if v == 0:
            return self.store_uint(0, bit_length)
        byte_length = (v.bit_length() + 7) // 8
        return self.store_uint(byte_length, bit_length).store_int(v, byte_length * 8)
    
    def store_coins(self, amount: int):
        return self.store_var_uint(amount, 16)
    
    def store_snake_bytes(self, b: bytes) -> Self:
        n = min(len(b), self.remaining_bits // 8)
        self.store_bytes(b[:n])
        b = b[n:]
        if b:
            self.store_ref(begin_cell().store_snake_bytes(b).end_cell())
        return self
    
    def store_snake_string(self, s: str) -> Self:
        return self.store_snake_bytes(s.encode())
    
    def store_hashmap(self, h: Hashmap) -> Self:
        from ..types.hashmap import store_hashmap
        store_hashmap(self, h)
        return self
    
    def store_hashmap_e(self, h: HashmapE) -> Self:
        if h is None:
            self.store_bit(0)
            return self
        return self.store_hashmap(h)

    def store_builder(self, b: Builder) -> Self:
        self.store_bits(b.data)
        for c in b.refs:
            self.store_ref(c)
        return self
    
    def store_tlb(self, o: TlbConstructor) -> Builder:
        return o.serialize(self)
    
    def store_maybe_tlb(self, o: TlbConstructor | None) -> Builder:
        if o is None:
            return self.store_bit(0)
        self.store_bit(1)
        return o.serialize(self)
    
    def store_ref_tlb(self, o: TlbConstructor) -> Builder:
        return self.store_ref(o.to_cell())
    
    def store_maybe_ref_tlb(self, o: TlbConstructor | None) -> Builder:
        return self.store_maybe_ref(None if o is None else o.to_cell())
    
    def store_address(self, a: Address) -> Builder:
        return self.store_tlb(a)
    
    def store_msg_address(self, a: MsgAddress) -> Builder:
        return self.store_tlb(a)
    
    def store_msg_address_int(self, a: MsgAddressInt) -> Builder:
        return self.store_tlb(a)
    
    def store_msg_address_ext(self, a: MsgAddressExt) -> Builder:
        return self.store_tlb(a)
    
    def store_maybe_ref(self, c: Cell | None) -> Builder:
        if c is None:
            return self.store_bit(0)
        self.store_bit(1)
        return self.store_ref(c)
    
    def store_slice(self, s: Slice) -> Self:
        b = s.to_cell().to_builder()
        return self.store_builder(b)

def begin_cell() -> Builder:
    return Builder()
