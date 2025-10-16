from __future__ import annotations

from dataclasses import dataclass
from typing import Self, Type

from ..cell.slice import Slice
from ..cell.cell import Cell
from ..cell.builder import Builder, begin_cell

from .tlb import TlbConstructor

from .msg_address import MsgAddressInt, MsgAddressExt, AddrNone
from .state_init import StateInit
from .common_msg_info import CommonMsgInfo, IntMsgInfo, ExtInInfo, ExtOutInfo
from .common_msg_info import common_msg_info
from .currency_collection import CurrencyCollection, ExtraCurrencyCollection

@dataclass(frozen=True, slots=True)
class Message(TlbConstructor):
    '''
    message$_ {X:Type} info:CommonMsgInfo
        init:(Maybe (Either StateInit ^StateInit))
        body:(Either X ^X) = Message X;
    '''
    info: CommonMsgInfo
    init: StateInit | None
    body: Cell

    @classmethod
    def tag(cls):
        return None

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Message:
        info = s.load_tlb(common_msg_info)
        init: StateInit | None
        has_init = s.load_bit()
        if has_init:
            init_in_ref = s.load_bit()
            if init_in_ref:
                init = s.load_tlb(StateInit)
            else:
                init = StateInit.from_cell(s.load_ref())
        else:
            init = None
        body: Cell = s.to_cell()
        body_in_ref = s.load_bit()
        if body_in_ref:
            body = s.load_ref()
        return cls(info, init, body)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_tlb(self.info)
        if self.init is None:
            b.store_bit(0)
        else:
            b.store_bit(1)
            init = self.init.to_builder()
            can_inline_init = len(init.data) <= b.remaining_bits - 2 and len(init.refs) <= b.remaining_refs - 1
            if can_inline_init:
                b.store_bit(0)
                b.store_builder(init)
            else:
                b.store_bit(1)
                b.store_ref(init.end_cell())

        body = self.body.to_builder()
        can_inline_body = len(body.data) <= b.remaining_bits - 1 and len(body.refs) <= b.remaining_refs
        if can_inline_body:
            b.store_bit(0)
            b.store_builder(body)
        else:
            b.store_bit(1)
            b.store_ref(body.to_cell())
        return b
    
    @classmethod
    def internal(cls,
                 src: MsgAddressInt,
                 dest: MsgAddressInt,
                 value: int | CurrencyCollection,
                 body: Cell = Cell.empty(),
                 init: StateInit | None = None,
                 ihr_disabled: bool = True,
                 bounce: bool = True,
                 bounced: bool = False,
                 ihr_fee: int = 0,
                 fwd_fee: int = 0,
                 created_lt: int = 0,
                 created_at: int = 0,
                 ) -> Message:
        if isinstance(value, int):
            value = CurrencyCollection(value, ExtraCurrencyCollection())
    
        info = IntMsgInfo(
            ihr_disabled=ihr_disabled,
            bounce=bounce,
            bounced=bounced,
            src=src,
            dest=dest,
            value=value,
            ihr_fee=ihr_fee,
            fwd_fee=fwd_fee,
            created_lt=created_lt,
            created_at=created_at
        )
        return cls(info, init, body)

    @classmethod
    def external_out(cls,
                     src: MsgAddressInt,
                     body: Cell = Cell.empty(),
                     dest: MsgAddressExt = AddrNone(),
                     init: StateInit | None = None,
                     created_lt: int = 0,
                     created_at: int = 0) -> Message:
        info = ExtOutInfo(
            src=src,
            dest=dest,
            created_lt=created_lt,
            created_at=created_at
        )
        return cls(info, init, body)
    
    @classmethod
    def external_in(cls, *,
                     src: MsgAddressExt,
                     dest: MsgAddressInt,
                     body: Cell = Cell.empty(),
                     init: StateInit | None = None,
                     import_fee: int = 0) -> Message:
        info = ExtInInfo(
            src=src,
            dest=dest,
            import_fee=import_fee
        )
        return cls(info, init, body)

    def get_normalized_hash(self) -> bytes:
        if not isinstance(self.info, ExtInInfo):
            raise ValueError('Can calculate normalized hash only from External-in message')
        normalized_ext_in_info = ExtInInfo(
            src=AddrNone(),
            dest=self.info.dest,
            import_fee=0
        )
        c = (
            begin_cell()
            .store_tlb(normalized_ext_in_info)
            .store_maybe_ref(None)
            .store_bit(1) # Either bit
            .store_ref(self.body)
            .end_cell()
        )
        return c.hash()
