import base64

from typing import Literal

from .base_api_client import BaseApiClient
from .provider import Provider

from agton.ton import Cell, Slice, MsgAddressInt, Network
from agton.ton.types.tvm_value import TvmValue

def encode_tvm_value(v: TvmValue) -> str:
    if isinstance(v, int):
        return str(v)
        # return {
        #     'type': 'int257',
        #     'value': hex(v) 
        # }
    if isinstance(v, Cell):
        return v.to_boc().hex()
        # return {
        #     'type': 'cell',
        #     'value': v.to_boc().hex()
        # }
    if isinstance(v, Slice):
        return v.to_cell().to_boc().hex()
        # return {
        #     'type': 'slice',
        #     'value': v.to_cell().to_boc().hex()
        # }
    raise ValueError('Stack supports only int, Cell and Slice types')

def decode_tvm_value(d: dict) -> TvmValue:
    print(d)
    type_ = d.get('type')
    value = d.get('value')
    if type_ is None:
        raise ValueError('No type for tvm value')
    if value is None:
        raise ValueError('No value for tvm value')

    if type_ == 'num':
        return int(value, base=16)
    if type_ == 'cell':
        return Cell.from_boc(base64.b64decode(value))
    if type_ == 'slice':
        return Cell.from_boc(base64.b64decode(value)).to_slice()

    raise ValueError(f'Unexpected type for tvm value: {type_}')

class TonApiClient(Provider, BaseApiClient):
    def __init__(self, *,
                 net: Literal['testnet', 'mainnet'] = 'testnet',
                 api_key: str | None = None):
        host: str
        if net == 'mainnet':
            host = 'https://tonapi.io/'
        elif net == 'testnet':
            host = 'https://testnet.tonapi.io/'
        else:
            raise ValueError(f"Network should be 'mainnet' or 'testnet', but got {net}")

        BaseApiClient.__init__(self, host, api_key=('X-Api-Key', api_key) if api_key else None)


    def raw_run_get_method(self,
                        a: MsgAddressInt,
                        method_id: int,
                        stack: tuple[TvmValue, ...],
                        method: str | None = None) -> tuple[TvmValue, ...]:
        if method is None:
            raise ValueError('method_id as integer is not supported by TonApi')
        # data = {
        #     'args': [
        #         encode_tvm_value(v) for v in stack
        #     ]
        # }
        args = ''
        if stack:
            args = '?args=' + '&args='.join(encode_tvm_value(v) for v in stack)
            args += '&fix_order=true'
        url = f'/v2/blockchain/accounts/{a}/methods/{method}'
        if args:
            url += args
        print(self.base_url + url)
        r = self.post(url)
        print(r)
        s = r['stack']
        c = r['exit_code']
        if c != 0:
            raise ValueError(f'Non zero exit code during get method: {c}')
        return tuple(decode_tvm_value(v) for v in s)

    def raw_send_external_message(self, message: bytes):
        data = {
            'boc': message.hex()
        }
        return self.post('/v2/blockchain/message', json=data)
