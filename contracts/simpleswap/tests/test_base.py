from algosdk.v2client import algod, indexer

import unittest

from src.faucet import Faucet


class BaseTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        # Algod client configuration.
        cls.algod_address = "http://localhost:4001"
        cls.algod_token   = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        cls.algod_client  = algod.AlgodClient(
            algod_token=cls.algod_token,
            algod_address=cls.algod_address
        )
        # Indexer client configuration.
        cls.indexer_address = "http://localhost:8980"
        cls.indexer_token   = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        cls.indexer_client  = indexer.IndexerClient(
            indexer_token=cls.indexer_token,
            indexer_address=cls.indexer_address
        )
        # Faucet configuration.
        cls.faucet = Faucet(
            passphrase="<FAUCET_MNEMONIC>"
        )


if __name__ == "__main__":
    pass