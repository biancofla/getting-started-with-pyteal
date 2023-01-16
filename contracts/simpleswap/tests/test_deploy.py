from algosdk import (
    account,
    encoding
)

from tests.test_base import BaseTestCase
from src.contract_ops import *

import time 


class DeployTestCase(BaseTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super(DeployTestCase, cls).setUpClass()

        cls.creator_pk, cls.creator_addr = account.generate_account()

        cls.faucet.dispense(
            algod_client=cls.algod_client,
            receiver_addr=cls.creator_addr,
            # Total balance required is 415000 microAlgos:
            # * 100,000 is the minimum standard required balance;
            # * 100,000 is the per page creation application fee;
            # * (25,000 + 3,500 ) * 4 = 114,000 is the addition per integer entry;
            # * (25,000 + 25,000) * 2 = 50,000  is the addition per byte slice entry;
            # * 1000 is the transaction fee.
            amount=415_000
        )


    def test_deploy(self):
        app_id = deploy(
            algod_client=self.algod_client,
            creator_pk=self.creator_pk
        )

        self.assertGreater(app_id, -1)

        # Wait for indexer to catch-up newest algod updates.
        time.sleep(1)

        app_global_state = get_application_global_state(
            indexer_client=self.indexer_client,
            app_id=app_id
        )

        self.assertTrue("admin" in app_global_state.keys())

        admin_addr = encoding.encode_address(app_global_state["admin"])

        self.assertEqual(admin_addr, self.creator_addr)


if __name__ == "__main__":
    pass
