from __future__ import annotations

from dataclasses import dataclass
from typing import Self, Type

from ..cell.slice import Slice
from ..cell.builder import Builder

from .tlb import TlbConstructor

from .msg_address import MsgAddressInt, MsgAddressExt
from .currency_collection import CurrencyCollection


@dataclass(frozen=True, slots=True)
class IntMsgInfo(TlbConstructor):
    '''
    int_msg_info$0 ihr_disabled:Bool bounce:Bool bounced:Bool
    src:MsgAddressInt dest:MsgAddressInt 
    value:CurrencyCollection ihr_fee:Grams fwd_fee:Grams
    created_lt:uint64 created_at:uint32 = CommonMsgInfo;
    '''
    ihr_disabled: bool
    bounce: bool
    bounced: bool
    src: MsgAddressInt
    dest: MsgAddressInt
    value: CurrencyCollection
    ihr_fee: int
    fwd_fee: int
    created_lt: int
    created_at: int

    @classmethod
    def tag(cls):
        return 0b0, 1
    
    def serialize_fields(self, b: Builder) -> Builder:
        return (
            b
            .store_bool(self.ihr_disabled)
            .store_bool(self.bounce)
            .store_bool(self.bounced)
            .store_tlb(self.src)
            .store_tlb(self.dest)
            .store_tlb(self.value)
            .store_coins(self.ihr_fee)
            .store_coins(self.fwd_fee)
            .store_uint(self.created_lt, 64)
            .store_uint(self.created_at, 32)
        )

    @classmethod
    def deserialize_fields(cls, s: Slice) -> IntMsgInfo:
        ihr_disabled = s.load_bool()
        bounce = s.load_bool()
        bounced = s.load_bool()
        src = s.load_msg_address_int()
        dest = s.load_msg_address_int()
        value = s.load_tlb(CurrencyCollection)
        ihr_fee = s.load_coins()
        fwd_fee = s.load_coins()
        created_lt = s.load_uint(64)
        created_at = s.load_uint(32)

        return cls(ihr_disabled, bounce, bounced, src, dest, value, ihr_fee, fwd_fee, created_lt, created_at)


@dataclass(frozen=True, slots=True)
class ExtInInfo(TlbConstructor):
    '''
    ext_in_msg_info$10 src:MsgAddressExt dest:MsgAddressInt 
    import_fee:Grams = CommonMsgInfo;
    '''

    src: MsgAddressExt
    dest: MsgAddressInt
    import_fee: int

    @classmethod
    def tag(cls):
        return 0b10, 2

    def serialize_fields(self, b: Builder) -> Builder:
        return (
            b
            .store_tlb(self.src)
            .store_tlb(self.dest)
            .store_coins(self.import_fee)
        )

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        src = s.load_msg_address_ext()
        dest = s.load_msg_address_int()
        import_fee = s.load_coins()
        return cls(src, dest, import_fee)


@dataclass(frozen=True, slots=True)
class ExtOutInfo(TlbConstructor):
    '''
    ext_out_msg_info$11 src:MsgAddressInt dest:MsgAddressExt
        created_lt:uint64 created_at:uint32 = CommonMsgInfo;
    '''

    src: MsgAddressInt
    dest: MsgAddressExt
    created_lt: int
    created_at: int

    @classmethod
    def tag(cls):
        return 0b11, 2

    def serialize_fields(self, b: Builder) -> Builder:
        return (
            b
            .store_tlb(self.src)
            .store_tlb(self.dest)
            .store_uint(self.created_lt, 64)
            .store_uint(self.created_at, 32)
        )

    @classmethod
    def deserialize_fields(cls, s: Slice) -> ExtOutInfo:
        src = s.load_msg_address_int()
        dest = s.load_msg_address_ext()
        created_lt = s.load_uint(64)
        create_at = s.load_uint(32)
        return cls(src, dest, created_lt, create_at)

CommonMsgInfo = IntMsgInfo | ExtInInfo | ExtOutInfo

def common_msg_info(s: Slice) -> CommonMsgInfo:
    tag = s.preload_uint(2)
    match tag:
        case 0b00 | 0b01: return IntMsgInfo.deserialize(s)
        case 0b10: return ExtInInfo.deserialize(s)
        case 0b11: return ExtOutInfo.deserialize(s)
    assert False
