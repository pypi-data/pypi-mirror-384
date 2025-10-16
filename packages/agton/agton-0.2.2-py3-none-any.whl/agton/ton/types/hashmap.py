from __future__ import annotations

from typing import Callable, Self
from dataclasses import dataclass, field
from ..common import BitString, int2bs, bs2int

from ..cell import Slice
from ..cell import Builder, begin_cell
from ..cell import Cell

from .msg_address import MsgAddress, Address, msg_address

from .tlb import TlbDeserializationError

'''
hm_edge#_ {n:#} {X:Type} {l:#} {m:#} label:(HmLabel ~l n) 
          {n = (~m) + l} node:(HashmapNode m X) = Hashmap n X;

hmn_leaf#_ {X:Type} value:X = HashmapNode 0 X;
hmn_fork#_ {n:#} {X:Type} left:^(Hashmap n X) 
           right:^(Hashmap n X) = HashmapNode (n + 1) X;

hml_short$0 {m:#} {n:#} len:(Unary ~n) {n <= m} s:(n * Bit) = HmLabel ~n m;
hml_long$10 {m:#} n:(#<= m) s:(n * Bit) = HmLabel ~n m;
hml_same$11 {m:#} v:Bit n:(#<= m) = HmLabel ~n m;

unary_zero$0 = Unary ~0;
unary_succ$1 {n:#} x:(Unary ~n) = Unary ~(n + 1);

hme_empty$0 {n:#} {X:Type} = HashmapE n X;
hme_root$1 {n:#} {X:Type} root:^(Hashmap n X) = HashmapE n X;
'''

@dataclass
class Hashmap:
    label: BitString
    node: Leaf | Fork

    def to_dict(self) -> dict[BitString, Slice]:
        d = dict()
        match self.node:
            case Leaf(s):
                d[self.label] = s
                return d
            case Fork(l, r):
                left = l.to_dict()
                right = r.to_dict()
                for k, v in left.items():
                    d[self.label + BitString([0]) + k] = v
                for k, v in right.items():
                    d[self.label + BitString([1]) + k] = v
                return d

    @classmethod
    def from_dict(cls, d: dict[BitString, Slice]) -> Hashmap:
        def lcp(a: list[BitString]) -> int:
            # todo: Benchmark and maybe optimize, currently O(n * m)
            n = len(a)
            m = len(a[0])
            for i in range(m):
                b = a[0][i]
                for j in range(n):
                    if b != a[j][i]:
                        return i
            return n

        keys = list(d.keys())
        if len(keys) == 1:
            k = keys[0]
            return Hashmap(k, Leaf(d[k]))
        k = lcp(keys)
        label = keys[0][:k]

        ld: dict[BitString, Slice] = dict()
        rd: dict[BitString, Slice] = dict()
        for key in keys:
            if key[k] == 0:
                ld[BitString(key[k + 1:])] = d[key]
            elif key[k] == 1:
                rd[BitString(key[k + 1:])] = d[key]
        l = cls.from_dict(ld)
        r = cls.from_dict(rd)

        return cls(BitString(label), Fork(l, r))

HashmapE = Hashmap | None

@dataclass
class Leaf:
    value: Slice

@dataclass
class Fork:
    left: Hashmap
    right: Hashmap

def load_unary(s: Slice) -> int:
    ans = 0
    while s.load_bit() == 1:
        ans += 1
    return ans

def store_unary(b: Builder, n: int):
    for _ in range(n):
        b.store_bit(1)
    b.store_bit(0)

def load_hml_short(s: Slice, m: int) -> tuple[BitString, int]:
    s.skip_prefix(int2bs(0b0, 1))
    n = load_unary(s)
    if not (n <= m):
        raise TlbDeserializationError()
    return s.load_bits(n), n

def load_hml_long(s: Slice, m: int) -> tuple[BitString, int]:
    s.skip_prefix(int2bs(0b10, 2))
    n = s.load_uint(m.bit_length())
    return s.load_bits(n), n

def load_hml_same(s: Slice, m: int) -> tuple[BitString, int]:
    s.skip_prefix(int2bs(0b11, 2))
    v = s.load_bit()
    n = s.load_uint(m.bit_length())
    return BitString([v] * n), n

def load_label(s: Slice, m: int) -> tuple[BitString, int]:
    tag = s.preload_uint(2)
    match tag:
        case 0b00 | 0b01: return load_hml_short(s, m)
        case 0b10: return load_hml_long(s, m)
        case 0b11: return load_hml_same(s, m)
    assert False

def store_label(b: Builder, l: BitString, m: int):
    raise NotImplementedError

def load_node(s: Slice, n: int) -> Leaf | Fork:
    if n == 0:
        return Leaf(s)
    left = load_hashmap(s.load_ref().begin_parse(), n - 1)
    right = load_hashmap(s.load_ref().begin_parse(), n - 1)
    return Fork(left, right)

def store_node(b: Builder, n: int, node: Leaf | Fork):
    raise NotImplementedError

def load_hashmap(s: Slice, n: int) -> Hashmap:
    label, l = load_label(s, n)
    m = n - l
    node = load_node(s, m)
    return Hashmap(label, node)

def store_hashmap(b: Builder, h: Hashmap) -> Builder:
    raise NotImplementedError

@dataclass(frozen=True, slots=True)
class HashmapCodec[K, V]:
    k_de: Callable[[BitString], K] | None = None
    k_se: Callable[[K], BitString] | None = None
    v_de: Callable[[Slice], V] | None = None
    v_se: Callable[[V], Slice] | None = None

    def decode(self, hashmap: HashmapE) -> dict[K, V]:
        if self.k_de is None or self.v_de is None:
            raise ValueError('Deserializators are not set')
        d = {} if hashmap is None else hashmap.to_dict()
        return {self.k_de(k): self.v_de(v) for k, v in d.items()}
    
    def encode(self, d: dict[K, V]) -> HashmapE:
        if not d:
            return None
        if self.k_se is None or self.v_se is None:
            raise ValueError('Serializators are not set')
        cd = {self.k_se(k): self.v_se(v) for k, v in d.items()}
        hashmap = Hashmap.from_dict(cd)
        return hashmap
    
    def with_int_values(self, n: int) -> HashmapCodec[K, int]:
        def v_se(v: int) -> Slice:
            return begin_cell().store_int(v, n).to_slice()
        def v_de(s: Slice) -> int:
            return s.load_int(n)
        return HashmapCodec(self.k_de, self.k_se, v_de, v_se)
    
    def with_uint_values(self, n: int) -> HashmapCodec[K, int]:
        def v_se(v: int) -> Slice:
            return begin_cell().store_uint(v, n).to_slice()
        def v_de(s: Slice) -> int:
            return s.load_uint(n)
        return HashmapCodec(self.k_de, self.k_se, v_de, v_se)
    
    def with_var_uint_values(self, n: int) -> HashmapCodec[K, int]:
        def v_se(v: int) -> Slice:
            return begin_cell().store_var_uint(v, n).to_slice()
        def v_de(s: Slice) -> int:
            return s.load_var_uint(n)
        return HashmapCodec(self.k_de, self.k_se, v_de, v_se)
    
    def with_coins_values(self) -> HashmapCodec[K, int]:
        def v_se(v: int) -> Slice:
            return begin_cell().store_coins(v).to_slice()
        def v_de(s: Slice) -> int:
            return s.load_coins()
        return HashmapCodec(self.k_de, self.k_se, v_de, v_se)
    
    def with_snake_data_values(self) -> HashmapCodec[K, str]:
        raise NotImplementedError
    
    def with_msg_address_values(self) -> HashmapCodec[K, MsgAddress]:
        def v_se(v: MsgAddress) -> Slice:
            return begin_cell().store_tlb(v).to_slice()
        def v_de(s: Slice) -> MsgAddress:
            return s.load_msg_address()
        return HashmapCodec(self.k_de, self.k_se, v_de, v_se)
    
    def with_address_values(self) -> HashmapCodec[K, Address]:
        def v_se(v: Address) -> Slice:
            return begin_cell().store_tlb(v).to_slice()
        def v_de(s: Slice) -> Address:
            return s.load_tlb(Address)
        return HashmapCodec(self.k_de, self.k_se, v_de, v_se)
    
    def with_int_keys(self, n: int) -> HashmapCodec[int, V]:
        def k_se(v: int) -> BitString:
            return begin_cell().store_int(v, n).to_cell().data
        def k_de(b: BitString) -> int:
            return bs2int(b, signed=True)
        return HashmapCodec(k_de, k_se, self.v_de, self.v_se)
    
    def with_uint_keys(self, n: int) -> HashmapCodec[int, V]:
        def k_se(v: int) -> BitString:
            return begin_cell().store_uint(v, n).to_cell().data
        def k_de(b: BitString) -> int:
            return bs2int(b, signed=False)
        return HashmapCodec(k_de, k_se, self.v_de, self.v_se)
    
    def with_address_keys(self) -> HashmapCodec[Address, V]:
        def k_se(a: Address) -> BitString:
            return begin_cell().store_address(a).to_cell().data
        def k_de(b: BitString) -> Address:
            return Cell(b).begin_parse().load_address()
        return HashmapCodec(k_de, k_se, self.v_de, self.v_se)
