from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self

from ..cell.slice import Slice
from ..cell.builder import Builder

from .hashmap import HashmapE

from .tlb import TlbConstructor

@dataclass(frozen=True, slots=True)
class ExtraCurrencyCollection(TlbConstructor):
    """
    extra_currencies$_ dict:(HashmapE 32 (VarUInteger 32)) = ExtraCurrencyCollection;
    """
    dict: HashmapE = None

    @classmethod
    def tag(cls):
        return None

    def serialize_fields(self, b: Builder) -> Builder:
        return b.store_hashmap_e(self.dict)

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        dict = s.load_hashmap_e(32)
        return cls(dict)


@dataclass(frozen=True, slots=True)
class CurrencyCollection(TlbConstructor):
    """
    currencies$_ grams:Grams other:ExtraCurrencyCollection = CurrencyCollection;
    """
    grams: int
    other: ExtraCurrencyCollection

    @classmethod
    def tag(cls):
        return None

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_coins(self.grams)
        b.store_tlb(self.other)
        return b

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        grams = s.load_coins()
        other = s.load_tlb(ExtraCurrencyCollection)
        return cls(grams, other)
