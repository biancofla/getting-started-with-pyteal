from algosdk import account

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
            #   * (25,000 + 25,000) * 2 =  50,000 is the addition per byte slice entry;
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

        cls.new_rate_integer = 5
        cls.new_rate_decimal = 1

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

        cls.app_addr = logic.get_application_address(cls.app_id)

        cls.faucet.dispense(
            algod_client=cls.algod_client,
            receiver_addr=cls.app_addr, 
            # Total balance required is 300000 microAlgos:
            # * 100,000 is the minimum standard required balance;
            # * 200,000 is the minimum amount of microAlgos that the account 
            #   needs in order to handle two new ASAs.
            amount=300_000
        )

        optin_assets(
            algod_client=cls.algod_client,
            admin_pk=cls.sm_creator_pk,
            app_id=cls.app_id,
            asset_id_from=cls.token_a_id,
            asset_id_to=cls.token_b_id
        )

        send_asa(
            algod_client=cls.algod_client,
            sender_pk=cls.asa_creator_pk,
            receiver_addr=cls.app_addr,
            asset_id=cls.token_a_id,
            amount=1_000_000
        )
        send_asa(
            algod_client=cls.algod_client,
            sender_pk=cls.asa_creator_pk,
            receiver_addr=cls.app_addr,
            asset_id=cls.token_b_id,
            amount=1_000_000
        )

        optin_asa(
            algod_client=cls.algod_client,
            account_pk=cls.asa_user_pk,
            asset_id=cls.token_a_id
        )
        optin_asa(
            algod_client=cls.algod_client,
            account_pk=cls.asa_user_pk,
            asset_id=cls.token_b_id
        )

        send_asa(
            algod_client=cls.algod_client,
            sender_pk=cls.asa_creator_pk,
            receiver_addr=cls.asa_user_addr,
            asset_id=cls.token_a_id,
            amount=1_000_000
        )
        send_asa(
            algod_client=cls.algod_client,
            sender_pk=cls.asa_creator_pk,
            receiver_addr=cls.asa_user_addr,
            asset_id=cls.token_b_id,
            amount=1_000_000
        )

        set_rate(
            algod_client=cls.algod_client,
            admin_pk=cls.sm_creator_pk,
            app_id=cls.app_id,
            new_rate_integer=cls.new_rate_integer,
            new_rate_decimal=cls.new_rate_decimal
        )


    def test_swap(self):
        swap_cr = swap(
            algod_client=self.algod_client,
            account_pk=self.asa_user_pk,
            app_id=self.app_id,
            asset_id_from=self.token_a_id,
            asset_id_to=self.token_b_id,
            amount_to_swap=500_000
        )
        self.assertGreater(swap_cr, -1)

        swap_cr = swap(
            algod_client=self.algod_client,
            account_pk=self.asa_user_pk,
            app_id=self.app_id,
            asset_id_from=self.token_b_id,
            asset_id_to=self.token_a_id,
            amount_to_swap=500_000
        )
        self.assertGreater(swap_cr, -1)

        balances = {
            str(a["asset-id"]): a["amount"] 
            for a in get_account_info(self.algod_client, self.asa_user_addr)["assets"]
        }
        asset_a_balance = balances[str(self.token_a_id)]
        asset_b_balance = balances[str(self.token_b_id)]

        self.assertEqual(asset_a_balance, 1_500_000)
        self.assertEqual(asset_b_balance,   750_000)


    def test_swap_wrong_asset_amount(self):
        swap_cr = swap(
            algod_client=self.algod_client,
            account_pk=self.asa_user_pk,
            app_id=self.app_id,
            asset_id_from=self.token_a_id,
            asset_id_to=self.token_b_id,
            amount_to_swap=0
        )
        self.assertEqual(swap_cr, -1)


if __name__ == "__main__":
    pass
