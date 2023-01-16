from algosdk import (
    account,
    encoding
)

from tests.test_base import BaseTestCase
from src.contract_ops import *


class SwapTestCase(BaseTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super(SwapTestCase, cls).setUpClass()

        cls.sm_creator_pk, cls.sm_creator_addr = account.generate_account()

        cls.faucet.dispense(
            algod_client=cls.algod_client,
            receiver_addr=cls.sm_creator_addr, 
            # Total balance required is 620000 microAlgos:
            # 1) 415000 microAlgos are required to deploy the smart-contract:
            #   * 100,000 is the minimum standard required balance;
            #   * 100,000 is the per page creation application fee;
            #   * (25,000 + 3,500 ) * 4 = 114,000 is the addition per integer entry;
            #   * (25,000 + 25,000) * 2 = 50,000  is the addition per byte slice entry;
            #   * 1000 is the transaction fee.
            # 2) 204000 microAlgos are required to perform the smart-contract call 
            #    'optin_assets':
            #   * 200,000 is the minimum amount of microAlgos that the smart 
            #     contract needs in order to handle two new ASAs;
            #   * 4000 are the transactions fees (one payment transaction 
            #     + no-op smart-contract call with two inner transactions).
            # 3) 1000 microAlgos are required to perform the smart-contract call 
            #    'set_rate'.
            amount=620_000
        )

        cls.asa_creator_pk, cls.asa_creator_addr = account.generate_account()
        cls.asa_manager_pk, cls.asa_manager_addr = account.generate_account()

        cls.faucet.dispense(
            algod_client=cls.algod_client,
            receiver_addr=cls.asa_creator_addr, 
            # Total balance required is 306000 microAlgos:
            # 1) 302000 microAlgos are required in order to create and handle
            #    two ASAs:
            #   * 100,000 is the minimum standard required balance;
            #   * 200,000 is the minimum amount of microAlgos that the account 
            #     needs in order to handle two new ASAs;
            #   * 2000 are the transactions fees needed to perform two create
            #     ASA operations.
            # 2) 2000 microAlgos are required in order to cover ASAs transfers 
            #    to the contract.
            # 3) 2000 microAlgos are required to cover the payment ASAs transfer.
            amount=306_000
        )

        cls.asa_user_pk, cls.asa_user_addr = account.generate_account()
        
        cls.faucet.dispense(
            algod_client=cls.algod_client,
            receiver_addr=cls.asa_user_addr, 
            # Total balance required is 308000 microAlgos:
            # 1) 300000 microAlgos are required in order to handle two ASAs:
            #   * 100,000 is the minimum standard required balance;
            #   * 200,000 is the minimum amount of microAlgos that the account 
            #     needs in order to handle two new ASAs.
            #   8 2000 are the fee needed to perform two opt-in operations.
            # 2) 8000 are the fee required to perform two smart-contract calls 
            #    to the 'swap' method (3000 microAlgos per call).
            amount=308_000
        )

        cls.token_a_conf = {
            "unit_name" : "Token A",
            "asset_name": "token-a",
            "total"     : 1_000_000_000,
            "decimals"  : 6
        }
        cls.token_b_conf = {
            "unit_name" : "Token B",
            "asset_name": "token-b",
            "total"     : 1_000_000_000,
            "decimals"  : 6
        }

        cls.new_rate_integer = 5
        cls.new_rate_decimal = 1

    def test_swap(self):
        app_id = deploy(
            algod_client=self.algod_client,
            creator_pk=self.sm_creator_pk
        )
        self.assertGreater(app_id, -1)

        token_a_id = create_asa(
            algod_client=self.algod_client,
            asa_creator_pk=self.asa_creator_pk,
            asa_manager_pk=self.asa_manager_pk,
            token_conf=self.token_a_conf
        )
        self.assertGreater(token_a_id, -1)

        token_b_id = create_asa(
            algod_client=self.algod_client,
            asa_creator_pk=self.asa_creator_pk,
            asa_manager_pk=self.asa_manager_pk,
            token_conf=self.token_b_conf
        )
        self.assertGreater(token_b_id, -1)

        app_addr = logic.get_application_address(app_id)
        
        self.faucet.dispense(
            algod_client=self.algod_client,
            receiver_addr=app_addr, 
            # Total balance required is 300000 microAlgos:
            # * 100,000 is the minimum standard required balance;
            # * 200,000 is the minimum amount of microAlgos that the account 
            #   needs in order to handle two new ASAs.
            amount=300_000
        )

        optin_assets_cr = optin_assets(
            algod_client=self.algod_client,
            admin_pk=self.sm_creator_pk,
            app_id=app_id,
            asset_id_from=token_a_id,
            asset_id_to=token_b_id
        )
        self.assertGreater(optin_assets_cr, -1)

        send_asa_cr = send_asa(
            algod_client=self.algod_client,
            sender_pk=self.asa_creator_pk,
            receiver_addr=app_addr,
            asset_id=token_a_id,
            amount=1_000_000
        )
        self.assertGreater(send_asa_cr, -1)

        send_asa_cr = send_asa(
            algod_client=self.algod_client,
            sender_pk=self.asa_creator_pk,
            receiver_addr=app_addr,
            asset_id=token_b_id,
            amount=1_000_000
        )
        self.assertGreater(send_asa_cr, -1)

        optin_asa_cr = optin_asa(
            algod_client=self.algod_client,
            account_pk=self.asa_user_pk,
            asset_id=token_a_id
        )
        self.assertGreater(optin_asa_cr, -1)

        optin_asa_cr = optin_asa(
            algod_client=self.algod_client,
            account_pk=self.asa_user_pk,
            asset_id=token_b_id
        )
        self.assertGreater(optin_asa_cr, -1)

        send_asa_cr = send_asa(
            algod_client=self.algod_client,
            sender_pk=self.asa_creator_pk,
            receiver_addr=self.asa_user_addr,
            asset_id=token_a_id,
            amount=1_000_000
        )
        self.assertGreater(send_asa_cr, -1)
        
        send_asa_cr = send_asa(
            algod_client=self.algod_client,
            sender_pk=self.asa_creator_pk,
            receiver_addr=self.asa_user_addr,
            asset_id=token_b_id,
            amount=1_000_000
        )
        self.assertGreater(send_asa_cr, -1)

        set_rate_cr = set_rate(
            algod_client=self.algod_client,
            admin_pk=self.sm_creator_pk,
            app_id=app_id,
            new_rate_integer=self.new_rate_integer,
            new_rate_decimal=self.new_rate_decimal
        )
        self.assertGreater(set_rate_cr, -1)

        swap_cr = swap(
            algod_client=self.algod_client,
            account_pk=self.asa_user_pk,
            app_id=app_id,
            asset_id_from=token_a_id,
            asset_id_to=token_b_id,
            amount_to_swap=500_000
        )
        self.assertGreater(swap_cr, -1)

        swap_cr = swap(
            algod_client=self.algod_client,
            account_pk=self.asa_user_pk,
            app_id=app_id,
            asset_id_from=token_b_id,
            asset_id_to=token_a_id,
            amount_to_swap=500_000
        )
        self.assertGreater(swap_cr, -1)

        balances = {
            str(a["asset-id"]): a["amount"] 
            for a in get_account_info(self.algod_client, self.asa_user_addr)["assets"]
        }
        asset_a_balance = balances[str(token_a_id)]
        asset_b_balance = balances[str(token_b_id)]

        self.assertEqual(asset_a_balance, 1_500_000)
        self.assertEqual(asset_b_balance,   750_000)


if __name__ == "__main__":
    pass
