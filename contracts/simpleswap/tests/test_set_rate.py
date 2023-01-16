from algosdk import (
    account,
    encoding
)

from tests.test_base import BaseTestCase
from src.contract_ops import *

import time


class SetRateTestCase(BaseTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super(SetRateTestCase, cls).setUpClass()

        cls.admin_pk, cls.admin_addr = account.generate_account()

        cls.faucet.dispense(
            algod_client=cls.algod_client,
            receiver_addr=cls.admin_addr, 
            # Total balance required is 416000 microAlgos:
            # 1) 415000 microAlgos are required to deploy the smart-contract:
            #   * 100,000 is the minimum standard required balance;
            #   * 100,000 is the per page creation application fee;
            #   * (25,000 + 3,500 ) * 4 = 114,000 is the addition per integer entry;
            #   * (25,000 + 25,000) * 2 = 50,000  is the addition per byte slice entry;
            #   * 1000 is the transaction fee.
            # 2) 1000 microAlgos are the fee required to perform the smart-contract call 
            #    'set_rate'.
            amount=416_000
        )

        cls.new_rate_integer = 5
        cls.new_rate_decimal = 1


    def test_set_rate(self):
        app_id = deploy(
            algod_client=self.algod_client,
            creator_pk=self.admin_pk
        )

        self.assertGreater(app_id, -1)

        set_rate_cr = set_rate(
            algod_client=self.algod_client,
            admin_pk=self.admin_pk,
            app_id=app_id,
            new_rate_integer=5,
            new_rate_decimal=1
        )

        self.assertGreater(set_rate_cr, -1)

        # Wait for indexer to catch-up newest algod updates.
        time.sleep(1)

        app_global_state = get_application_global_state(
            indexer_client=self.indexer_client,
            app_id=app_id
        )

        self.assertTrue("R" in app_global_state.keys())
        self.assertTrue("r" in app_global_state.keys())

        rate_integer = app_global_state["R"]
        rate_decimal = app_global_state["r"]

        self.assertEqual(
            rate_integer * (10 ** - rate_decimal),
            self.new_rate_integer * (10 ** - self.new_rate_decimal),
        )


if __name__ == "__main__":
    pass
