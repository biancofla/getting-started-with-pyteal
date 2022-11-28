from algosdk.future import transaction
from algosdk.v2client import algod
from algosdk import (
    constants,
    account,
    error,
    logic
)

from pyteal import *

import hashlib
import base64
import os

SANDBOX_COMMAND_PATH = "../../../sandbox/sandbox"
GENESIS_ADDRESS      = "S4Z25GO6DW6ZL6FKX5O3YFFVQEXAMMPZQOGO7VP3LHKRWJUJHKRF5WOM4M"

algod_address = "http://localhost:4001"
algod_token   = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
algod_client  = algod.AlgodClient(algod_token, algod_address)

def feed_accounts(accounts):
    """
        Feed the accounts.

        Args:
            accounts (list): accounts to feed.
    """
    for account in accounts:
        os.system(
            f"{SANDBOX_COMMAND_PATH} goal clerk send -f {GENESIS_ADDRESS} -t {account[1]} -a 1000000"
        )

def deploy(creator_pk):
    """
        Deploy the smart contract.

        Args:
            * creator_pk (str): smart contract's creator private key.

        Returns:
            * (int): if successful, return the appilcation index of the
            deployed smart contract; otherwise, return -1.
    """
    with open("../../build/approval.teal", "r") as f: approval = f.read()
    with open("../../build/clear.teal"   , "r") as f: clear    = f.read()
    
    sender = account.address_from_private_key(creator_pk)

    try:
        approval_result  = algod_client.compile(approval)
        approval_program = base64.b64decode(approval_result["result"])

        clear_result  = algod_client.compile(clear)
        clear_program = base64.b64decode(clear_result["result"])
        
        local_schema  = transaction.StateSchema(num_uints=1, num_byte_slices=3)
        global_schema = transaction.StateSchema(num_uints=0, num_byte_slices=0)

        suggested_parameters = algod_client.suggested_params()

        unsigned_txnn = transaction.ApplicationCreateTxn(
            sender=sender,
            sp=suggested_parameters,
            on_complete=transaction.OnComplete.NoOpOC,
            approval_program=approval_program,
            clear_program=clear_program,
            global_schema=global_schema,
            local_schema=local_schema
        )
        signed_txn = unsigned_txnn.sign(creator_pk)

        txn_id = algod_client.send_transaction(signed_txn)

        result = transaction.wait_for_confirmation(
            algod_client=algod_client,
            txid=txn_id,
            wait_rounds=2
        )

        app_id = result["application-index"]

        return app_id
    except error.AlgodHTTPError as e:
        print(e)
        return -1

def optin(account_pk, app_id):
    sender = account.address_from_private_key(account_pk)
    try:
        suggested_parameters = algod_client.suggested_params()

        unsigned_txn = transaction.ApplicationOptInTxn(
            sender=sender,
            sp=suggested_parameters,
            index=app_id
        )
        signed_txn = unsigned_txn.sign(account_pk)

        txn_id = algod_client.send_transaction(signed_txn)

        result = transaction.wait_for_confirmation(
            algod_client=algod_client,
            txid=txn_id,
            wait_rounds=2
        )

        confirmation_round = result["confirmed-round"]

        return confirmation_round
    except error.AlgodHTTPError as e:
        print(e)
        return -1

def create_challenge(challenger_pk, challenge, app_id):
    sender = account.address_from_private_key(challenger_pk)
    try:
        suggested_parameters = algod_client.suggested_params()

        app_args = []
        app_args.append("challenge".encode())
        app_args.append(sha256b64(challenge).encode())

        unsigned_txn_1 = transaction.ApplicationNoOpTxn(
            sender=sender,
            sp=suggested_parameters,
            index=app_id,
            app_args=app_args,
            rekey_to=constants.ZERO_ADDRESS
        )
        unsigned_txn_2 = transaction.PaymentTxn(
            sender=sender,
            sp=suggested_parameters,
            receiver=logic.get_application_address(app_id),
            amt=5000,
            close_remainder_to=constants.ZERO_ADDRESS,
            rekey_to=constants.ZERO_ADDRESS
        )

        group_id = transaction.calculate_group_id(
            [unsigned_txn_1, unsigned_txn_2]
        )
        unsigned_txn_1.group = group_id
        unsigned_txn_2.group = group_id

        signed_txn_1 = unsigned_txn_1.sign(challenger_pk)
        signed_txn_2 = unsigned_txn_2.sign(challenger_pk)

        signed_group = [signed_txn_1, signed_txn_2]

        txn_id = algod_client.send_transactions(signed_group)

        result = transaction.wait_for_confirmation(
            algod_client=algod_client,
            txnid=txn_id,
            wait_rounds=4
        )

        confirmation_round = result["confirmed-round"]

        return confirmation_round
    except error.AlgodHTTPError as e:
        print(e)
        return -1

def get_local_state(address, app_id):
    """
        Get application's local state.

        Args:
            * address (str): account's address.
            * app_id (int): application index.

        Returns:
            (dict): application's local state.
    """
    local_state = {}
    try:
        account_info = algod_client.account_info(address)
        for ls in account_info["apps-local-state"]:
            if ls["id"] == app_id:
                local_state = ls["key-value"]
                break
    except error.AlgodHTTPError as e:
        print(e)
    finally:
        return local_state

def sha256b64(s: str) -> str:
    return base64.b64encode(
        hashlib.sha256(str(s).encode("utf-8")).digest()
    ).decode("utf-8")

def test():
    accounts = [account.generate_account() for _ in range(0, 3)]

    feed_accounts(accounts)

    app_id = deploy(creator_pk=accounts[0][0])
    
    optin_account_1 = optin(accounts[1][0], app_id)
    optin_account_2 = optin(accounts[2][0], app_id)
    if optin_account_1 > -1 and optin_account_2 > -1:
        print(get_local_state(accounts[1][1], app_id))
        print(get_local_state(accounts[2][1], app_id))

        # confirmation_round = create_challenge(
        #     accounts[1][0],
        #     "r",
        #     app_id
        # )
        # if confirmation_round > -1:
        #     print(get_local_state(accounts[1][1], app_id))

if __name__ == "__main__":
    test()