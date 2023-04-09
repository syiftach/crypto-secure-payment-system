from ex1.utils import BlockHash
from ex1.transaction import Transaction
from typing import List
from hashlib import sha256


class Block:
    # implement __init__ as you see fit.
    def __init__(self, txs, prev_block_hash):
        self.size = len(txs)
        self._txs: List[Transaction] = txs
        self._prev_block_hash = prev_block_hash
        # create block-hash
        h = sha256()
        h.update(prev_block_hash)
        for tx in txs:
            h.update(tx.get_txid())
        self._block_id = BlockHash(h.digest())

    def __repr__(self):
        return f'Block-{self.get_block_hash().hex()[:4]}'

    def __str__(self):
        return f'Block-{self.get_block_hash().hex()[:4]};size={self.size}'

    def get_block_hash(self) -> BlockHash:
        """returns hash of this block"""
        return self._block_id

    def get_transactions(self) -> List[Transaction]:
        """returns the list of transactions in this block."""
        return self._txs

    def get_prev_block_hash(self) -> BlockHash:
        """Gets the hash of the previous block in the chain"""
        return self._prev_block_hash
