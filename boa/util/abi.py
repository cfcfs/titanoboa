# wrapper module around whatever encoder we are using
from typing import Annotated, Any

from eth.codecs.abi.decoder import Decoder
from eth.codecs.abi.encoder import Encoder
from eth.codecs.abi.exceptions import ABIError
from eth.codecs.abi.nodes import ABITypeNode
from eth.codecs.abi.parser import Parser
from eth_typing import Address as PYEVM_Address
from eth_utils import to_canonical_address, to_checksum_address

from boa.util.lrudict import lrudict


# XXX: inherit from bytes directly so that we can pass it to py-evm?
# inherit from `str` so that ABI encoder / decoder can work without failing
class Address(str):  # (PYEVM_Address):
    # converting between checksum and canonical addresses is a hotspot;
    # this class contains both and caches recently seen conversions
    __slots__ = ("canonical_address",)
    _cache = lrudict(1024)

    canonical_address: Annotated[PYEVM_Address, "canonical address"]

    def __new__(cls, address):
        if isinstance(address, Address):
            return address

        try:
            return cls._cache[address]
        except KeyError:
            pass

        checksum_address = to_checksum_address(address)
        self = super().__new__(cls, checksum_address)
        self.canonical_address = to_canonical_address(address)
        cls._cache[address] = self
        return self

    # def __hash__(self):
    #    return hash(self.checksum_address)

    # def __eq__(self, other):
    #    return super().__eq__(self, other)

    def __repr__(self):
        checksum_addr = super().__repr__()
        return f"_Address({checksum_addr})"


_parsers: dict[str, ABITypeNode] = {}


def _get_parser(schema: str):
    try:
        return _parsers[schema]
    except KeyError:
        _parsers[schema] = (ret := Parser.parse(schema))
        return ret


def abi_encode(schema: str, data: Any) -> bytes:
    return Encoder.encode(_get_parser(schema), data)


def abi_decode(schema: str, data: bytes) -> Any:
    return Decoder.decode(_get_parser(schema), data)


def is_abi_encodable(abi_type: str, data: Any) -> bool:
    try:
        abi_encode(abi_type, data)
        return True
    except ABIError:
        return False
