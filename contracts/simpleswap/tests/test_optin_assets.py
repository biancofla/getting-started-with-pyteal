from algosdk import account

from tests.test_base import BaseTestCase
from src.contract_ops import *

import time


class OptinAssetsTestCase(BaseTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super(OptinAssetsTestCase, cls).setUpClass()

        cls.sm_creator_pk, cls.sm_creator_addr = account.generate_account()

        cls.faucet.dispense(
            algod_client=cls.algod_client,
            receiver_addr=cls.sm_creator_addr, 
            # Total balance required is 619000 microAlgos:
            # 1) 415000 microAlgos are required to deploy the smart-contract:
            #   * 100,000 is the minimum standard required balance;
            #   * 100,000 is the per page creation application fee;
            #   * (25,000 + 3,500 ) * 4 = 114,000 is the addition per integer entry;
            #   * (25,000 + 25,000) * 2 =  50,000 is the addition per byte slice entry;
            #   * 1000 is the transaction fees.
            # 2) 204000 microAlgos are required to perform the smart-contract call 
            #    'optin_assets':
            #   * 200,000 is the minimum amount of microAlgos that the smart 
            #     contract needs in order to handle two new ASAs;
            #   * 4000 are the transactions fees (one payment transaction 
            #     + no-op smart-contract call with two inner transactions).
            amount=619_000
        )

        cls.asa_creator_pk, cls.asa_creator_addr = account.generate_account()
        cls.asa_manager_pk, cls.asa_manager_addr = account.generate_account()

        cls.faucet.dispense(
            algod_client=cls.algod_client,
            receiver_addr=cls.asa_creator_addr, 
            # Total balance required is 302000 microAlgos:
            # * 100,000 is the minimum standard required balance;
            # * 200,000 is the minimum amount of microAlgos that the account 
            #   needs in order to handle two new ASAs;
            # * 2000 are the transactions fees needed to perform two ASAs
            #   creation operations.
            amount=302_000
        )

        cls.app_id = deploy(
            algod_client=cls.algod_client,
            creator_pk=cls.sm_creator_pk
        )

        cls.token_a_conf = {
            "unit_name" : "Token A",
            "asset_name": "token-a",
            "total"     : 1_000_000_000,
            "decimals"  : 6
        }
        cls.token_a_id = create_asa(
            algod_client=cls.algod_client,
            asa_creator_pk=cls.asa_creator_pk,
            asa_manager_pk=cls.asa_manager_pk,
            token_conf=cls.token_a_conf
        )

        cls.token_b_conf = {
            "unit_name" : "Token B",
            "asset_name": "token-b",
            "total"     : 1_000_000_000,
            "decimals"  : 6
        }
        cls.token_b_id = create_asa(
            algod_client=cls.algod_client,
            asa_creator_pk=cls.asa_creator_pk,
            asa_manager_pk=cls.asa_manager_pk,
            token_conf=cls.token_b_conf
        )

        cls.faucet.dispense(
            algod_client=cls.algod_client,
            receiver_addr=logic.get_application_address(cls.app_id), 
            # Total balance required is 300000 microAlgos:
            # * 100,000 is the minimum standard required balance;
            # * 200,000 is the minimum amount of microAlgos that the account 
            #   needs in order to handle two new ASAs.
            amount=300_000
        )


    def test_optin_assets(self):
        optin_assets_cr = optin_assets(
            algod_client=self.algod_client,
            admin_pk=self.sm_creator_pk,
            app_id=self.app_id,
            asset_id_from=self.token_a_id,
            asset_id_to=self.token_b_id
        )
        self.assertGreater(optin_assets_cr, -1)

        # Wait for indexer to catch-up newest algod updates.
        time.sleep(1)

        app_global_state = get_application_global_state(
            indexer_client=self.indexer_client,
            app_id=self.app_id
        )

        asset_id_from = app_global_state["asset-id-from"]
        asset_id_to   = app_global_state["asset-id-to"]

        self.assertEqual(self.token_a_id, asset_id_from)
        self.assertEqual(self.token_b_id, asset_id_to)


    def test_optin_assets_double_optin(self):
        optin_assets_cr = optin_assets(
            algod_client=self.algod_client,
            admin_pk=self.sm_creator_pk,
            app_id=self.app_id,
            asset_id_from=self.token_a_id,
            asset_id_to=self.token_b_id
        )
        self.assertEqual(optin_assets_cr, -1)


if __name__ == "__main__":
    pass
