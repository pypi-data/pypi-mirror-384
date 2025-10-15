from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Self, Iterable, TYPE_CHECKING
from bitarray import bitarray, frozenbitarray
from bitarray.util import ba2int
from hashlib import sha256

from agton.ton.common.bitstring import BitString

from ..crypto.signing import sign, verify

if TYPE_CHECKING:
    from .slice import Slice
    from .builder import Builder

MAX_BITS: int = 1023
MAX_REFS: int = 4

class CellType(Enum):
    ordinary = -1
    pruned_branch = 1
    library_ref = 2
    merkle_proof = 3
    merkle_update = 4


class LevelMask(int):
    def __new__(cls, value: int):
        return super().__new__(cls, value)
    
    def level(self) -> int:
        return self.bit_length()
    
    def hash_index(self) -> int:
        return self.bit_count()
    
    def hashes_count(self) -> int:
        return self.hash_index() + 1
    
    def apply(self, level: int) -> LevelMask:
        return LevelMask(self & ((1 << level) - 1))
    
    def is_significant(self, level: int) -> bool:
        if level == 0:
            return True
        return bool(self >> (level - 1) & 1)


class Cell:
    def __init__(self,
                 data: BitString,
                 refs: Iterable[Self] = (),
                 special: bool = False) -> None:
        self.data = data
        self.refs = tuple(refs)
        self.special = special

        self.type = self._get_type_and_check()
        self.level_mask = self._get_mask()

        self._depthes: list[int] = []
        self._hashes: list[bytes] = []
        self._calculate_hashes_and_depthes()

    def _get_type_and_check(self) -> CellType:
        if not self.special:
            if len(self.refs) > MAX_REFS:
                raise ValueError(f"Ordinary cell can have at most {MAX_REFS} references, got {len(self.refs)}")
            if len(self.data) > MAX_BITS:
                raise ValueError(f"Ordinary cell can have at most {MAX_BITS} bits in data, got {len(self.data)}")
            return CellType.ordinary
        else:
            if len(self.data) < 8:
                raise ValueError(f"Special cell must have at least 8 bits in data")
            t = ba2int(self.data[:8])
            if t == CellType.pruned_branch.value:
                m = ba2int(self.data[8:16])
                h = m.bit_count()
                if not (1 <= m <= 7 and 
                        len(self.refs) == 0 and 
                        len(self.data) == 16 + 8 * (h * 32 + h * 2)):
                    raise ValueError(f"Pruned branch is invalid")
                return CellType.pruned_branch
            elif t == CellType.library_ref.value:
                if not (len(self.refs) == 0 and len(self.data) == 8 + 256):
                    raise ValueError(f"Library cell is invalid")
                return CellType.library_ref
            elif t == CellType.merkle_proof.value:
                if not (len(self.refs) == 1 and len(self.data) == 280):
                    raise ValueError(f"Merkle proof cell is invalid")
                return CellType.merkle_proof
            elif t == CellType.merkle_update.value:
                if not (len(self.refs) == 2 and len(self.data) == 552):
                    raise ValueError(f"Merkle update cell is invalid")
                return CellType.merkle_update
            else:
                raise ValueError(f"Unknown cell type: {t}")
    
    def _get_mask(self) -> LevelMask:
        if self.type == CellType.ordinary:
            m = 0
            for c in self.refs:
                m |= c.level_mask
            return LevelMask(m)
        elif self.type == CellType.pruned_branch:
            return LevelMask(ba2int(self.data[8:16]))
        elif self.type == CellType.merkle_proof:
            return LevelMask(self.refs[0].level_mask >> 1)
        elif self.type == CellType.merkle_update:
            return LevelMask((self.refs[0].level_mask | self.refs[1].level_mask) >> 1)
        elif self.type == CellType.library_ref:
            return LevelMask(0)
        else:
            assert False
    
    def _get_refs_descriptor(self, level_mask: LevelMask) -> bytes:
        d = len(self.refs) + 8 * self.special + 32 * level_mask.level()
        return d.to_bytes(1, 'big')

    def _get_bits_descriptor(self) -> bytes:
        b = len(self.data)
        d = b // 8 + (b + 7) // 8
        return d.to_bytes(1, 'big')

    def _get_descriptors(self, level_mask: LevelMask = LevelMask(0)) -> bytes:
        return self._get_refs_descriptor(level_mask) + self._get_bits_descriptor()

    def depth(self, level: int | None = None) -> int:
        if level is None:
            level = self.level_mask.level()
        hash_index = self.level_mask.apply(level).hash_index()
        if self.type == CellType.pruned_branch:
            pruned_hash_index = self.level_mask.hash_index()
            if hash_index != pruned_hash_index:
                off = 2 + 32 * pruned_hash_index + hash_index * 2
                return int.from_bytes(self._get_data_bytes()[off: off + 2], 'big')
            hash_index = 0
        return self._depthes[hash_index]

    def hash(self, level: int | None = None) -> bytes:
        if level is None:
            level = self.level_mask.level()
        hash_index = self.level_mask.apply(level).hash_index()
        if self.type == CellType.pruned_branch:
            pruned_hash_index = self.level_mask.hash_index()
            if hash_index != pruned_hash_index:
                return self._get_data_bytes()[2 + (hash_index * 32): 2 + ((hash_index + 1) * 32)]
            hash_index = 0
        return self._hashes[hash_index]
    
    def _calculate_hashes_and_depthes(self) -> None:
        total_hash_count = self.level_mask.hashes_count()
        hash_count = total_hash_count
        if self.type == CellType.pruned_branch:
            hash_count = 1
        hash_index_offset = total_hash_count - hash_count
        hash_index = 0
        level = self.level_mask.level()
        for li in range(0, level + 1):
            if not self.level_mask.is_significant(li):
                continue
            if li < hash_index_offset:
                hash_index += 1
                continue
            dsc = self._get_descriptors(self.level_mask.apply(li))
            hasher = sha256(dsc)
            if hash_index == hash_index_offset:
                if li != 0 and self.type != CellType.pruned_branch:
                    raise ValueError('not pruned or 0')
                data = self._get_data_bytes()
                hasher.update(data)
            else:
                if li == 0 or self.type == CellType.pruned_branch:
                    raise ValueError('not pruned or 0')
                off = hash_index - hash_index_offset - 1
                hasher.update(self._hashes[off])
            depth = 0
            for r in self.refs:
                if self.type in (CellType.merkle_proof, CellType.merkle_update):
                    ref_depth = r.depth(li + 1)
                else:
                    ref_depth = r.depth(li)
                depth_bytes = ref_depth.to_bytes(2, 'big')
                hasher.update(depth_bytes)
                depth = max(depth, ref_depth + 1)

            if depth >= 1024:
                raise ValueError('depth is more than max depth')
            for r in self.refs:
                if self.type in (CellType.merkle_proof, CellType.merkle_update):
                    hasher.update(r.hash(li + 1))
                else:
                    hasher.update(r.hash(li))
            off = hash_index - hash_index_offset
            self._depthes.append(depth)
            self._hashes.append(hasher.digest())
            hash_index += 1

    def _get_data_bytes(self) -> bytes:
        result = bitarray(self.data)
        if len(result) % 8:
            result.append(1)
            result.fill()
        return result.tobytes()

    @classmethod
    def empty(cls) -> Cell:
        return cls(data=frozenbitarray(), refs=(), special=False)

    def to_boc(self, 
               with_crc=False,
               with_index=False,
               with_cache=False,
               with_top_hash=False,
               with_int_hashes=False) -> bytes:
        from .boc import encode
        return encode([self], with_crc, with_index, with_cache, with_top_hash, with_int_hashes)
    
    @classmethod
    def from_boc(cls, b: bytes | str) -> Cell:
        from .boc import decode
        if isinstance(b, str):
            b = bytes.fromhex(b)
        roots = decode(b)
        if len(roots) != 1:
            raise ValueError(f'Expected exactly one root in BoC, but {len(roots)} found')
        return roots[0]
    
    def begin_parse(self, allow_exotic: bool = False) -> Slice:
        from .slice import Slice
        if not allow_exotic and self.special:
            raise ValueError('Cannot parse exotic cell, use allow_exotic=True if you want to parse exotic internals')
        return Slice(self, 0, len(self.data), 0, len(self.refs))
    
    def to_slice(self, allow_exotic: bool = False):
        return self.begin_parse(allow_exotic)
    
    def to_builder(self) -> Builder:
        from .builder import Builder
        if self.special:
            raise ValueError("Can't convert special cell to builder")
        b = Builder()
        b.data = bitarray(self.data)
        b.refs = list(self.refs)
        return b
    
    def sign(self, private_key: bytes) -> bytes:
        return sign(self.hash(), private_key)
    
    def verify(self, signature: bytes, public_key: bytes) -> bool:
        return verify(self.hash(), signature, public_key)

    def _type_description(self):
        desc = ''
        if self.type == CellType.pruned_branch:
            desc = '* Prunned Branch '
        elif self.type == CellType.merkle_proof:
            desc = '* Merkle Proof '
        elif self.type == CellType.merkle_update:
            desc = '* Merkle Update '
        elif self.type == CellType.library_ref:
            desc = '* Lirary Ref '
        return desc

    def dump(self, d: int = 0, comma: bool = False) -> str:
        desc = self._type_description()
        data = f'{len(self.data)}[{self.data.tobytes().hex().upper()}]'
        refs = ''
        if self.refs:
            refs = ' -> {\n'
            for c in self.refs[:-1]:
                refs += '\t' * d + '\t' + c.dump(d + 1, comma=True) + '\n'
            refs += '\t' * d + '\t' + self.refs[-1].dump(d + 1) + '\n'
            refs += '\t' * d + '}'
        return desc + data + refs + (',' if comma else '')

    def __hash__(self) -> int:
        return hash(self.hash())
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Cell):
            return False
        return self.hash() == other.hash()

    def __repr__(self) -> str:
        desc = self._type_description()
        return f"Cell({desc}{len(self.data)}[{self.data.tobytes().hex().upper()}] -> {len(self.refs)} refs)"

    def __str__(self) -> str:
        return self.dump()
