from ex1.utils import *
from ex1.transaction import Transaction
from ex1.bank import Bank
from ex1.block import Block
from typing import Optional, List, Union


class Wallet:
    def __init__(self) -> None:
        """This function generates a new wallet with a new private key."""
        pvt_key, pub_key = gen_keys()
        # private key
        self._pvt_key = pvt_key
        # public key/address
        self._pub_key = pub_key
        # current balance
        self._balance = 0
        # hash of last block that the wallet was updated by
        self._latest_block_hash = GENESIS_BLOCK_PREV
        # unspent transactions that represents coins a wallet has
        self._unspent_coins = set()
        # pending tx/coin transfer requests that were created, and still were not approved
        self._pending_spent_coins = set()
        # transaction that was created by the this wallet, and pending: still not part of a block
        self._pending_txs = set()
        # history of approved transaction that are in some block,
        # and their output equals the wallet's address
        self._income_txs = set()
        # history of approved transaction that are in some block,
        # and the output of their input transaction equals this wallet's address
        self._outcome_txs = set()

    def __repr__(self):
        return f'Wallet-{self.get_address().hex()[:4]}'

    def __str__(self):
        return f'Wallet-{self.get_address().hex()[:4]};Balance={self.get_balance()}'

    def update(self, bank: Bank) -> None:
        """
        This function updates the balance allocated to this wallet by querying the bank.
        Don't read all of the bank's utxo, but rather process the blocks since the last update one at a time.
        For this exercise, there is no need to validate all transactions in the block.
        """
        # get new blocks to update from
        new_blocks = self._get_new_blocks(bank)
        # if there are new blocks to be updated by
        for block in new_blocks:
            for tx in block.get_transactions():
                # if coin is transferred to my account
                if tx.output == self._pub_key:
                    self._balance += 1
                    self._income_txs.add(tx)
                    self._unspent_coins.add(tx)
                # if coin is transferred from my account
                prev_tx = self._get_previous_tx(tx, bank)
                if prev_tx is not None and prev_tx.output == self._pub_key:
                    # assert self._balance >= 1
                    self._balance -= 1
                    self._outcome_txs.add(tx)
                    self._pending_txs.discard(tx)  # it is a tx that self created
                    # remove the corresponding coin from pending spent coins
                    self._pending_spent_coins.discard(self._get_previous_tx(tx, bank))

    def create_transaction(self, target: PublicKey) -> Optional[Transaction]:
        """
        This function returns a signed transaction that moves an unspent coin to the target.
        It chooses the coin based on the unspent coins that this wallet had since the last update.
        If the wallet already spent a specific coin, but that transaction wasn't confirmed by the
        bank just yet (it still wasn't included in a block) then the wallet  shouldn't spend it again
        until unfreeze_all() is called.
        The method returns None if there are no unspent outputs that can be used.
        """
        # if there is coin available to spend
        if self._balance > 0:
            # try to spend an available coin
            for tx in self._unspent_coins:
                # create a new transaction
                raw_data = tx.get_txid() + target  # raw data to be hashed by sha256
                new_tx = Transaction(target, tx.get_txid(), sign(raw_data, self._pvt_key))
                self._pending_txs.add(new_tx)  # add new-tx to pending set
                self._pending_spent_coins.add(tx)  # mark as pended spent coin
                self._unspent_coins.discard(tx)  # remove the coin from available coins
                return new_tx
        return None

    def unfreeze_all(self) -> None:
        """
        Allows the wallet to try to re-spend outputs that it created transactions for
        (unless these outputs made it into the blockchain).
        """
        # move all currently pending-spent-coins to the unspent-coins set
        # thus, the wallet can try to re-spend the pended spent coin
        self._unspent_coins = self._unspent_coins.union(self._pending_spent_coins)

    def get_balance(self) -> int:
        """
        This function returns the number of coins that this wallet has.
        It will return the balance according to information gained when update() was last called.
        Coins that the wallet owned and sent away will still be considered as part of the balance until the spending
        transaction is in the blockchain.
        """
        return self._balance

    def get_address(self) -> PublicKey:
        """
        This function returns the public address of this wallet (see the utils module for generating keys).
        """
        return self._pub_key

    # ===================================== PROTECTED_METHODS ========================================= #

    def _get_new_blocks(self, bank) -> List[Block]:
        new_blocks = []
        # complete the blockchain going backwards until reaching a block that the wallet has
        current_hash = bank.get_latest_hash()
        while self._latest_block_hash != current_hash:
            block = bank.get_block(current_hash)
            new_blocks.insert(0, block)
            # update current block hash (go to previous block in the blockchain)
            current_hash = block.get_prev_block_hash()
        # update the last seen block hash
        self._latest_block_hash = bank.get_latest_hash()
        return new_blocks

    def _get_previous_tx(self, tx: Transaction, bank: Bank) -> Union[Transaction, None]:
        current_hash = bank.get_latest_hash()
        while current_hash != GENESIS_BLOCK_PREV:
            current_block = bank.get_block(current_hash)
            for tx_other in current_block.get_transactions():
                # if tx-other txid is equal to input-txid of given tx
                if tx_other.get_txid() == tx.input:
                    return tx_other
            # update the current hash to previous block in the chain
            current_hash = current_block.get_prev_block_hash()
        return None
