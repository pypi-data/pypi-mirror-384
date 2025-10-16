# agton
## Tour
### TVM primitives: `Cell`, `Slice` and `Builder`
```py
from agton.ton import Cell, begin_cell

c1 = (
    begin_cell()
    .store_uint(1337, 32)
    .store_maybe_ref(
        begin_cell()
        .store_coins(200)
        .end_cell()
    )
    .end_cell()
)

boc = c1.to_boc()
c2 = Cell.from_boc(boc)
assert c1.hash() == c2.hash()
assert c1 == c2 # Actually compares Cell.hash() under the hood

cs = c1.begin_parse()
assert cs.load_uint(32) == 1337
inner = cs.load_maybe_ref()
assert inner is not None
cs = inner.begin_parse()
assert cs.load_coins() == 200

print(c1) # full tree
# 33[0000053980] -> {
#         12[1C80]
# }
print(repr(c1)) # Cell(33[0000053980] -> 1 refs)

def count_bits(c: Cell) -> int:
    ans = 0
    for b in c.data:
        ans += b
    for r in c.refs:
        ans += count_bits(r)
    return ans
```

### Address
Addresses in TON are rather complex, and agton mirrors the exact tlb definitions. However `agton.ton` exports `Address` that is inteded to be used in most cases. `Address` is exactly `AddrStd`, even with `anycast:(Maybe Anycast)`

```py
# All types related to MsgAddress
from agton.ton import Address, MsgAddress, MsgAddressInt, MsgAddressExt
from agton.ton.types.msg_address import AddrNone, AddrExtern, AddrVar, AddrStd

from agton.ton import StateInit, Cell, begin_cell

Address(-1, bytes([0] * 32)) # Ef8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADAU

state_init = StateInit(code=Cell.empty(), data=Cell.empty())
Address(0, state_init.to_cell().hash())

a = Address.parse('UQCBirB-586qkioRmyqPgn9y3_GVaXMl_mA9MBxt2BK__Iyp')

assert isinstance(a, MsgAddressInt)
assert isinstance(a, MsgAddress)
assert not isinstance(a, MsgAddressExt)

b = begin_cell().store_address(a)
assert b.to_slice().load_address() == a

a0: Address       = b.to_slice().load_address()
a1: MsgAddress    = b.to_slice().load_msg_address()
a2: MsgAddressInt = b.to_slice().load_msg_address_int()
# a3: MsgAddressExt = b.to_slice().load_msg_address_ext()
# ^ Will trigger a TlbDeserializationError
# cause it isn't an external address stored in b

print(a)         # EQCBirB-586qkioRmyqPgn9y3_GVaXMl_mA9MBxt2BK__NFs
print(f"{a:n}")  # UQCBirB-586qkioRmyqPgn9y3_GVaXMl_mA9MBxt2BK__Iyp
print(f"{a:t}")  # kQCBirB-586qkioRmyqPgn9y3_GVaXMl_mA9MBxt2BK__Grm
print(f"{a:nt}") # 0QCBirB-586qkioRmyqPgn9y3_GVaXMl_mA9MBxt2BK__Dcj
print(f"{a:r}")  # 0:818ab07ee7ceaa922a119b2a8f827f72dff195697325fe603d301c6dd812bffc
print(a.raw())   # 0:818ab07ee7ceaa922a119b2a8f827f72dff195697325fe603d301c6dd812bffc
```

### TL-B
`agton.ton` offers a powerful abstract class `TlbConstructor`. Every class inherited from `TlbConstructor` must implement three methods

```python
@classmethod
def tag(cls) -> tuple[int, int] | None: ...

@classmethod
def deserialize_fields(cls, s: Slice) -> Self: ...

def serialize_fields(cls, b: Builder) -> Builder: ...
```

Every `TlbConstructor` gains a lot of flexibility. Let's look at the example

```python
from dataclasses import dataclass
from typing import Self
from agton.ton import TlbConstructor, Builder, Slice, begin_cell

@dataclass(frozen=True)
class Point(TlbConstructor):
    ''' point#3f x:int64 y:int64 = Point; '''
    x: int
    y: int

    @classmethod
    def tag(cls):
        return 0x3f, 8

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        x = s.load_int(64)
        y = s.load_int(64)
        return cls(x, y)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_int(self.x, 64)
        b.store_int(self.y, 64)
        return b

p = Point(5, -10)

cell_with_point = p.to_cell()
assert p == Point.from_cell(cell_with_point)

cell_with_point = begin_cell().store_tlb(p).end_cell() # We can store tlb constructor
p = cell_with_point.begin_parse().load_tlb(Point)      # We can also load tlb constructor
```

But `TlbConstructor` is not exactly a `TlbType`. `TlbType` is a union of multiple constructors. Let's look at the example of true `TlbType`

```python
@dataclass(frozen=True)
class Circle(TlbConstructor):
    ''' circle$01 p:Point r:uint64 = Shape; '''
    p: Point
    r: int

    @classmethod
    def tag(cls):
        return 0b01, 2

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        p = s.load_tlb(Point)
        r = s.load_uint(64)
        return cls(p, r)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_tlb(self.p)
        b.store_uint(self.r, 64)
        return b

@dataclass(frozen=True)
class Line(TlbConstructor):
    ''' line$10 a:Point b:uint64 = Shape; '''
    a: Point
    b: Point

    @classmethod
    def tag(cls):
        return 0b10, 2

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        a = s.load_tlb(Point)
        b = s.load_tlb(Point)
        return cls(a, b)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_tlb(self.a)
        b.store_tlb(self.b)
        return b

Shape = Circle | Line
```

Here `Shape` is a true `TlbType`, and we still can do pretty cool thing with it

```python
from random import randrange as rand

def get_shape() -> Shape:
    p1 = Point(rand(10), rand(10))
    p2 = Point(rand(10), rand(10))
    if rand(2):
        return Circle(p1, rand(20))
    return Line(p1, p2)

circle: Shape = get_shape()
cell_with_shape = begin_cell().store_tlb(circle).end_cell()
```

We can store tlb union types, cause we know the constructor. But there is a problem, we can't easily load tlb union types, we need to load tlb constructor based on tags

`cs.load_tlb(Shape)` – this does not work cause we don't know how to deserialize shape, and sadly python does not allow to define static methods on union types, but there is a solution! At least partial...

```python
def shape(s: Slice) -> Shape:
    tag_len = Circle.tag()[1] # 2 bits
    tag = s.preload_uint(tag_len)
    if tag == Circle.tag()[0]:
        return Circle.deserialize(s)
    if tag == Line.tag()[0]:
        return Line.deserialize(s)
    raise ValueError(f'Unknown tag: {tag}')

s: Shape = cell_with_shape.begin_parse().load_tlb(shape) # now we can load a Shape!
match s:
    case Circle(p, r): print(f'Circle at {p} with radius={r}')
    case Line(a, b): print(f'Line from {a} to {b}')
```

So what exactly `Slice.load_tlb` does? It's defined like this:

```python
def load_tlb[T: TlbConstructor](self, deserializer: type[T] | Callable[[Slice], T]) -> T:
    if isinstance(deserializer, type):
        cls = cast(type[T], deserializer)
        return cls.deserialize(self)
    else:
        t = deserializer(self)
        return t
```

`deserializer` is either a
1. `type[TlbConstructor]`
2. `(Slice) -> TlbConstructor`

The first case is useful when we know the exact constructor that was used or the tlb type has only one constructor. We used the first case when we did `cs.load_tlb(Point)`, and the second case when we were loading a `Shape` – we defined `(Slice) -> TlbConstructor` function

### Hashmap

Hashmap are by far the most complex tlb structure, and sadly it is impossible to implement it at agton as true collections of `TlbConstructor`'s (`TlbConstructor`'s do not support `~` operator), but still working with `Hashmap` is pretty convenient and close to tvm hashmaps.

```python
from agton.ton import HashmapCodec, begin_cell

squares = {x: x * x for x in range(-6, 12, 3)}
# {-6: 36, -3: 9, 0: 0, 3: 9, 6: 36, 9: 81}

hashmap_codec = HashmapCodec().with_int_keys(32).with_uint_values(64)
squares_hashmap = hashmap_codec.encode(squares)
# squares_hashmap is HashmapE type
# HashmapE = Hashmap | None

c = begin_cell().store_hashmap_e(squares_hashmap).end_cell() # Storing is not yet implemented :) But would be
cs = c.begin_parse()
new_squares_hashmap = cs.load_hashmap_e(32) # Loading is implemented
new_squares = hashmap_codec.decode(new_squares_hashmap) 
assert set(squares.items()) == set(new_squares.items())
```

Also `Hashmap` has methods, that operates with the canonical hashmap representation (BitString -> Slice)

```python
class Hashmap:
    to_dict(self) -> dict[BitString, Slice]: ...

    @classmethod
    def from_dict(cls, d: dict[BitString, Slice]) -> Hashmap: ...
```

## Contract and Provider
`Provider` is an interface to implement your own contract provider, it basically defines only two user-facing methods
```python
class Provider(ABC):
    def send_external_message(self, message: Message | Cell | bytes) -> bytes:
    def run_get_method(
        self,
        a: MsgAddressInt,
        method_id: int | str,
        stack: Iterable[TvmValue] | TvmValue | None = None
    ) -> tuple[TvmValue, ...] | TvmValue
```

`agton.ton` implements only one provider `ToncenterClient` for now, but this is the basis for the future sandbox feature

One can also implement `EmptyProvider`
```
class EmptyProvider(Provider):
    def send_external_message(...): raise ValueError
    def run_get_method(...): raise ValueError
```
With that provider all contracts should continue to work as long as contracts do not call any get methods

`agton.ton` gives you a `Contract` type. `Contract` basically holds address of a contract and a provider and gives you convenient methods 
```python
Contract.create_internal_message(
    value: int | CurrencyCollection = 0,
    body: Cell = Cell.empty()
    init: StateInit | None = None,
    bounce: bool = True
) -> MessageRelaxed

Contract.create_external_message(
    src: MsgAddressExt = AddrNone(),
    body: Cell = Cell.empty()
) -> Message

Contract.run_get_method(
    method_id: int | str,
    stack: Iterable[TvmValue] | TvmValue | None = None
) -> tuple[TvmValue, ...] | TvmValue
```

`Contract` is intended to be used for a wrappers, here is simplest example of it's use case
```python
from dataclasses import dataclass
from typing import Self
from agton.ton import (
    ToncenterClient, Contract,
    TlbConstructor, Address, MessageRelaxed, CurrencyCollection,
    Builder, Slice, to_nano
)

@dataclass(frozen=True)
class Increase(TlbConstructor):
    ''' increase#0978f14e by:uint32 '''
    by: int

    @classmethod
    def tag(cls):
        return 0x0978f14e, 32

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        by = s.load_uint(32)
        return cls(by)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_uint(self.by, 32)
        return b


class Counter(Contract):
    def create_increase_message(
                self,
                by: int,
                value: int | CurrencyCollection = to_nano(0.2)
            ) -> MessageRelaxed:
        return self.create_internal_message(
            value=value,
            body=Increase(by).to_cell()
        )
    
    def get_counter(self) -> int:
        s = self.provider.run_get_method(self.address, 'counter')
        match s:
            case int(): return s
            case _: raise TypeError(f'Unexpected result stack for get_counter: {s!r}')


provider = ToncenterClient(net='testnet')
counter_address = Address.parse('I am too lazy to actually deploy counter')
counter = Counter(provider, counter_address)

print(counter.get_counter())
message: MessageRelaxed = counter.create_increase_message(3)
assert message.info.dest == counter.address
```
Notice that `message` in the example above is `MessageRelaxed`, that is an internal message. With `message.info.dest` equal to `conuter.address`. We can't simply send it to blockchain, we need to send it via sender somehow. `agton.wallet` implements different wallets (currently only WalletV3R2) so you can send it via wallets implemented there
