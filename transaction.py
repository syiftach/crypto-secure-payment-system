from ex1.utils import PublicKey, TxID, Signature
from typing import Optional
from hashlib import sha256

NEW_COIN_SIG_LEN = 48


class Transaction:
    """Represents a transaction that moves a single coin
    A transaction with no source creates money. It will only be created by the bank."""

    def __init__(self, output: PublicKey, input: Optional[TxID], signature: Signature) -> None:
        # do not change the name of this field:
        self.output: PublicKey = output
        # do not change the name of this field:
        self.input: Optional[TxID] = input
        # do not change the name of this field:
        self.signature: Signature = signature
        # generate txid out of the transaction's content
        h = sha256()
        if self.input is None or not isinstance(self.input, bytes):
            h.update(self.output + self.signature)
        else:
            h.update(self.input + self.output + self.signature)
        self._txid = TxID(h.digest())

    def __repr__(self):
        return f'Tx-{self.get_txid().hex()[:4]}'

    def __str__(self):
        return f'Tx-{self.get_txid().hex()[:4]}'

    def __eq__(self, other):
        return self._txid == other.get_txid()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._txid)

    def get_txid(self) -> TxID:
        """Returns the identifier of this transaction. This is the SHA256 of the transaction contents."""
        return self._txid

    # ===================================== PROTECTED_METHODS ========================================= #

    def _is_new_coin_tx(self):
        return self.input is None and len(self.signature) == NEW_COIN_SIG_LEN
