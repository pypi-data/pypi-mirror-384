from typing import Self
from dataclasses import dataclass

from ..cell.slice import Slice
from ..cell.cell import Cell
from ..cell.builder import Builder

from .tlb import TlbConstructor

@dataclass(frozen=True, slots=True)
class TickTock(TlbConstructor):
    '''tick_tock$_ tick:Bool tock:Bool = TickTock;'''
    tick: bool
    tock: bool

    @classmethod
    def tag(cls):
        return None

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_bool(self.tick)
        b.store_bool(self.tock)
        return b

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        tick = s.load_bool()
        tock = s.load_bool()
        return cls(tick, tock)


@dataclass(frozen=True, slots=True)
class StateInit(TlbConstructor):
    '''
    _ fixed_prefix_length:(Maybe (## 5)) special:(Maybe TickTock)
      code:(Maybe ^Cell) data:(Maybe ^Cell)
      library:(Maybe ^Cell) = StateInit;
    '''
    fixed_prefix_length: int | None = None
    special: TickTock | None = None
    code: Cell | None = None
    data: Cell | None = None
    library: Cell | None = None

    @classmethod
    def tag(cls):
        return None

    def serialize_fields(self, b: Builder | None = None) -> Builder:
        if b is None:
            b = Builder()
        if self.fixed_prefix_length is not None:
            b.store_bit(1)
            b.store_uint(self.fixed_prefix_length, 5)
        else:
            b.store_bit(0)
        b.store_maybe_tlb(self.special)
        b.store_maybe_ref(self.code)
        b.store_maybe_ref(self.data)
        b.store_maybe_ref(self.library)
        return b

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        fixed_prefix_length = s.load_uint(5) if s.load_bit() else None
        special = s.load_tlb(TickTock)
        code = s.load_maybe_ref()
        data = s.load_maybe_ref()
        library = s.load_maybe_ref()
        return cls(fixed_prefix_length, special, code, data, library)
