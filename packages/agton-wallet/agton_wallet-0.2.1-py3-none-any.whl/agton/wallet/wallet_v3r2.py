from __future__ import annotations

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Iterable

from agton.ton import Contract, Cell, Message, MessageRelaxed, begin_cell, Provider, TlbConstructor
from agton.ton import Builder
from agton.ton import Slice
from agton.ton.crypto.signing import private_key_to_public_key

from agton.wallet.mnemonic import mnemonic_to_private_key, new_mnemonic

WALLET_V3R2_CODE = Cell.from_boc('b5ee9c720101010100710000deff0020dd2082014c97ba218201339cbab19f71b0ed44d0d31fd31f31d70bffe304e0a4f2608308d71820d31fd31fd31ff82313bbf263ed44d0d31fd31fd3ffd15132baf2a15144baf2a204f901541055f910f2a3f8009320d74a96d307d402fb00e8d101a4c8cb1fcb1fcbffc9ed54')
WALLET_V3R2_SUBWALLET_MAGIC = 698983191

@dataclass(frozen=True, slots=True)
class WalletV3R2Data(TlbConstructor):
    seqno: int
    subwallet: int
    public_key: bytes

    @classmethod
    def initial(cls, public_key: bytes, subwallet: int) -> WalletV3R2Data:
        return cls(
            seqno=0,
            subwallet=subwallet,
            public_key=public_key
        )
    
    @classmethod
    def tag(cls):
        return None

    @classmethod
    def deserialize_fields(cls, s: Slice) -> WalletV3R2Data:
        seqno = s.load_uint(32)
        subwallet = s.load_uint(32)
        public_key = s.load_bytes(256 // 8)
        return cls(seqno, subwallet, public_key)

    def serialize_fields(self, b: Builder) -> Builder:
        return (
            b
            .store_uint(self.seqno, 32)
            .store_uint(self.subwallet, 32)
            .store_bytes(self.public_key)
        )


class WalletV3R2(Contract):
    def __init__(self,
                 provider: Provider,
                 private_key: bytes,
                 subwallet: int | None = None,
                 wc: int = 0) -> None:
        if subwallet is None:
            subwallet = WALLET_V3R2_SUBWALLET_MAGIC + wc
        self.subwallet = subwallet
        self.private_key = private_key

        public_key = private_key_to_public_key(self.private_key)
        initial_data = WalletV3R2Data.initial(public_key, self.subwallet).to_cell()
        address = WalletV3R2.code_and_data_to_address(WALLET_V3R2_CODE, initial_data)
        super().__init__(provider, address)

    MessageWithMode = tuple[MessageRelaxed, int]

    def create_signed_external(self, messages_with_modes: Iterable[MessageWithMode], valid_until: int, seqno: int) -> Message:
        messages_with_modes = tuple(messages_with_modes)
        if len(messages_with_modes) > 4:
            raise ValueError('WalletV3R2 supports only up to 4 messages')
        packed_messages: Builder = Builder()
        for message, mode in messages_with_modes:
            packed_messages.store_uint(mode, 8)
            packed_messages.store_ref(message.to_cell())

        unsigned_body = (
            begin_cell()
            .store_uint(self.subwallet, 32)
            .store_uint(valid_until, 32)
            .store_uint(seqno, 32)
            .store_builder(packed_messages)
        )
        signature = unsigned_body.end_cell().sign(self.private_key)
        signed_body = (
            begin_cell()
            .store_bytes(signature)
            .store_builder(unsigned_body)
            .end_cell()
        )
        return self.create_external_message(signed_body)
    
    def _safety_check(self, mode: int, allow_dangerous: bool):
        if not (mode & 2) and not allow_dangerous:
            raise ValueError(
                'Sending message without SendIgnoreErrors flag set can be dangerous'
                'use alow_dangerous=True if you know what you doing, and want to suppress this error'
            )

    def send(self,
             m: MessageRelaxed,
             valid_until: int | None = None,
             mode: int = 3,
             *, 
             allow_dangerous: bool = False) -> bytes:
        self._safety_check(mode, allow_dangerous)
        if valid_until is None:
            t = datetime.now() + timedelta(minutes=3)
            valid_until = int(t.timestamp())
        signed_message = self.create_signed_external([(m, mode)], valid_until, self.seqno())
        return self.provider.send_external_message(signed_message)
    
    def send_many(self,
                  messages_with_modes: Iterable[MessageWithMode],
                  valid_until: int | None = None, 
                  *, 
                  allow_dangerous: bool = False) -> bytes:
        messages_with_modes = tuple(messages_with_modes)
        for _, mode in messages_with_modes:
            self._safety_check(mode, allow_dangerous)

        if valid_until is None:
            t = datetime.now() + timedelta(minutes=3)
            valid_until = int(t.timestamp())
        signed_message = self.create_signed_external(messages_with_modes, valid_until, self.seqno())
        return self.provider.send_external_message(signed_message)
    
    def seqno(self) -> int:
        s = self.run_get_method('seqno')
        match s:
            case int(): return s
            case _: raise TypeError(f'Unexpected result for seqno: {s!r}')
    
    @classmethod
    def from_private_key(cls,
                         provider: Provider,
                         private_key: bytes,
                         subwallet: int | None = None,
                         wc: int = 0) -> WalletV3R2:
        return cls(provider, private_key, subwallet, wc)

    @classmethod
    def from_mnemonic(cls,
                      provider: Provider,
                      mnemonic: str,
                      subwallet: int | None = None,
                      wc: int = 0) -> WalletV3R2:
        private_key = mnemonic_to_private_key(mnemonic)
        return cls.from_private_key(provider, private_key, subwallet, wc)

    @classmethod
    def create(cls,
               provider: Provider,
               subwallet: int | None = None,
               wc: int = 0) -> tuple[WalletV3R2, str]:
        mnemonic = new_mnemonic()
        return cls.from_mnemonic(provider, mnemonic, subwallet, wc), mnemonic
