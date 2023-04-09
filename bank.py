# from .utils import BlockHash, PublicKey, verify, gen_keys, sign, GENESIS_BLOCK_PREV
from ex1.transaction import Transaction, NEW_COIN_SIG_LEN
from ex1.block import Block
from typing import List, Set, Union

from secrets import token_bytes
from ex1.utils import *


class Bank:
    def __init__(self) -> None:
        """Creates a bank with an empty blockchain and an empty mempool."""
        self._blockchain: List[Block] = []
        self._mempool: List[Transaction] = []
        self._utxo: List[Transaction] = []

    def __str__(self):
        return f'Bank;size={len(self._blockchain)}'

    def add_transaction_to_mempool(self, transaction: Transaction) -> bool:
        """
        This function inserts the given transaction to the mempool.
        It will return False iff one of the following conditions hold:
        (i) the transaction is invalid (the signature fails)
        (ii) the source doesn't have the coin that he tries to spend
        (iii) there is contradicting tx in the mempool.
        (iv) there is no input (i.e., this is an attempt to create money from nothing)
        """
        if self._validate_tx(transaction):
            self._mempool.append(transaction)
            return True
        return False

    def end_day(self, limit: int = 10) -> BlockHash:
        """
        This function tells the bank that the day ended,
        and that the first `limit` transactions in the mempool should be committed to the blockchain.
        If there are fewer than 'limit' transactions in the mempool, a smaller block is created.
        If there are no transactions, an empty block is created. The hash of the block is returned.
        """
        if not isinstance(limit, int) or limit < 0:
            raise ValueError('limit must be non-negative integer')
        idx = min(limit, len(self._mempool))
        # take the the first "limit" transactions, and commit them
        to_commit_txs = self._mempool[:idx]
        # new pending transactions (uncommitted transactions)
        new_mempool = self._mempool[idx:]
        # update the utxo ledger
        self._update_utxo(to_commit_txs)
        # update mempool and create a new block and add it to the blockchain
        self._mempool = new_mempool
        new_block = Block(to_commit_txs, self.get_latest_hash())
        self._blockchain.append(new_block)
        return new_block.get_block_hash()

    def get_block(self, block_hash: BlockHash) -> Block:
        """
        This function returns a block object given its hash. If the block doesnt exist, an exception is thrown..
        """
        for block in self._blockchain:
            if block.get_block_hash() == block_hash:
                return block
        raise ValueError('block does not exist in the blockchain')

    def get_latest_hash(self) -> BlockHash:
        """
        This function returns the hash of the last Block that was created by the bank.
        """
        if len(self._blockchain) > 0:
            return self._blockchain[-1].get_block_hash()
        return GENESIS_BLOCK_PREV

    def get_mempool(self) -> List[Transaction]:
        """
        This function returns the list of transactions that didn't enter any block yet.
        """
        return self._mempool

    def get_utxo(self) -> List[Transaction]:
        """
        This function returns the list of unspent transactions.
        """
        return self._utxo

    def create_money(self, target: PublicKey) -> None:
        """
        This function inserts a transaction into the mempool that creates a single coin out of thin air.
        Instead of a signature, this transaction includes a random string of 48 bytes (so that every two creation
         transactions are different).
        This function is a secret function that only the bank can use (currently for tests, and will make sense in a
        later exercise).
        """
        signature = token_bytes(NEW_COIN_SIG_LEN)
        # create new coin transaction
        new_coin_tx = Transaction(target, None, signature)
        self._mempool.append(new_coin_tx)

    # ===================================== PROTECTED_METHODS ========================================= #

    def _get_previous_tx(self, tx: Transaction) -> Union[Transaction, None]:
        txs_history = self._get_txs_history()
        for tx_other in txs_history:
            # if tx-other txid is equal to input-txid of given tx
            if tx_other.get_txid() == tx.input:
                return tx_other
        return None

    def _validate_tx(self, tx: Transaction) -> bool:
        # check if given tx is an illegal new-coin-tx
        if tx.input is None and len(tx.signature) == NEW_COIN_SIG_LEN:
            return False
        # check the signature:
        # verify that the given tx's signature satisfies the output of its input-tx
        prev_tx = self._get_previous_tx(tx)
        raw_data = tx.input + tx.output
        if prev_tx is None or not verify(raw_data, tx.signature, prev_tx.output):
            return False
        # check coin availability:
        # make sure that the input-transaction is in the utxo ledger
        if prev_tx not in self._utxo:
            return False
        # check if there is a contradicting tx:
        # a different tx that has the same input txid
        if self._contradicting_tx(tx):
            return False
        return True

    def _contradicting_tx(self, tx: Transaction) -> bool:
        # two transactions are contradicting each other if their input is pointing to the same tx
        for tx_other in self._mempool:
            if tx_other.input == tx.input:
                return True
        return False

    def _update_utxo(self, to_commit_txs) -> None:
        # txids of transactions that are used as an input of other transaction
        used_tx_ids = {tx.input for tx in to_commit_txs if tx.input is not None}
        # union of all previous transactions and those to commit, which has an unspent output
        temp_utxo = set(self._utxo).union(to_commit_txs)
        # update the utxo of the bank to all transactions that was not used an input for other transactions
        self._utxo = [tx for tx in temp_utxo if tx.get_txid() not in used_tx_ids]

    def _get_txs_history(self) -> Set[Transaction]:
        txs_history = set(self._mempool).union(self._utxo)
        for block in self._blockchain:
            for tx in block.get_transactions():
                txs_history.add(tx)
        return txs_history
