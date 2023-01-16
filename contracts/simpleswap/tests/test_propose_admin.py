from algosdk import account, encoding

from tests.test_base import BaseTestCase
from src.contract_ops import *

import time


class ProposeAdminTestCase(BaseTestCase):
    
    @classmethod
    def setUpClass(cls) -> None:
        super(ProposeAdminTestCase, cls).setUpClass()

        cls.admin_pk    , cls.admin_addr     = account.generate_account()
        cls.new_admin_pk, cls.new_admin_addr = account.generate_account()

        cls.faucet.dispense(
            algod_client=cls.algod_client,
            receiver_addr=cls.admin_addr, 
            # Total balance required is 416000 microAlgos:
            # 1) 415000 microAlgos are required to deploy the smart-contract:
            #   * 100,000 is the minimum standard required balance;
            #   * 100,000 is the per page creation application fee;
            #   * (25,000 + 3,500 ) * 4 = 114,000 is the addition per integer entry;
            #   * (25,000 + 25,000) * 2 =  50,000 is the addition per byte slice entry;
            #   * 1000 is the transaction fee.
            # 2) 1000 microAlgos are the fee required to perform the smart-contract call 
            #    'propose_admin'.
            amount=416_000
        )

        cls.app_id = deploy(
            algod_client=cls.algod_client,
            creator_pk=cls.admin_pk
        )


    def test_propose_admin(self):
        propose_admin_cr = propose_admin(
            algod_client=self.algod_client,
            admin_pk=self.admin_pk,
            app_id=self.app_id,
            admin_proposal_addr=self.new_admin_addr
        )
        self.assertGreater(propose_admin_cr, -1)

        # Wait for indexer to catch-up newest algod updates.
        time.sleep(1)

        app_global_state = get_application_global_state(
            indexer_client=self.indexer_client,
            app_id=self.app_id
        )
        self.assertTrue("admin-proposal" in app_global_state.keys())

        app_admin_proposal_addr = encoding.encode_address(app_global_state["admin-proposal"])

        self.assertEqual(app_admin_proposal_addr, self.new_admin_addr)


    def test_propose_admin_wrong_admin(self):
        propose_admin_cr = propose_admin(
            algod_client=self.algod_client,
            admin_pk=self.new_admin_pk,
            app_id=self.app_id,
            admin_proposal_addr=self.new_admin_addr
        )
        self.assertEqual(propose_admin_cr, -1)


if __name__ == "__main__":
    pass
