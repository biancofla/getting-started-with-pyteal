from algosdk.future import transaction
from algosdk.v2client import algod
from algosdk import (
    account,
    error
)

from pyteal import *

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
        
        local_schema  = transaction.StateSchema(num_uints=0, num_byte_slices=0)
        global_schema = transaction.StateSchema(num_uints=1, num_byte_slices=1)

        suggested_parameters = algod_client.suggested_params()

        unsigned_txn = transaction.ApplicationCreateTxn(
            sender=sender,
            sp=suggested_parameters,
            on_complete=transaction.OnComplete.NoOpOC,
            approval_program=approval_program,
            clear_program=clear_program,
            global_schema=global_schema,
            local_schema=local_schema
        )
        signed_txn = unsigned_txn.sign(creator_pk)

        tx_id = algod_client.send_transaction(signed_txn)

        result = transaction.wait_for_confirmation(
            algod_client=algod_client,
            txid=tx_id,
            wait_rounds=2
        )

        app_id = result["application-index"]

        return app_id
    except error.AlgodHTTPError as e:
        print(e)
        return -1

def modify_counter(account_pk, app_id, increase=True):
    """
        Modify smart contract's global counter.

        Args:
            * account_pk (str): account's private key.
            * app_id (int): application index.
            * increase (bool, default=True): if True, 
            increase the counter; otherwise, decrease the counter.

        Returns:
            * (int): if successful, return the confirmation round; 
            otherwise, return -1.
    """
    sender = account.address_from_private_key(account_pk)
    try:
        suggested_parameters = algod_client.suggested_params()

        app_args = []
        if increase: app_args.append("inc".encode())
        else: app_args.append("dec".encode())

        unsigned_txn = transaction.ApplicationNoOpTxn(
            sender=sender,
            sp=suggested_parameters,
            index=app_id,
            app_args=app_args
        )
        signed_txn = unsigned_txn.sign(account_pk)

        tx_id = algod_client.send_transaction(signed_txn)

        result = transaction.wait_for_confirmation(
            algod_client=algod_client,
            txid=tx_id,
            wait_rounds=2
        )

        confirmation_round = result["confirmed-round"]

        return confirmation_round
    except error.AlgodHTTPError as e:
        print(e)
        return -1

def get_global_state(app_id):
    """
        Get application's global state.

        Args:
            * app_id (int): application index.
        Returns:
            * (dict): application's global state.
    """
    global_state = {}
    try:
        app_info = algod_client.application_info(app_id)

        global_state = app_info["params"]["global-state"]
    except error.AlgodHTTPError as e:
        print(e)
    finally:
        return global_state

def test():
    accounts = [account.generate_account() for _ in range(0, 2)]

    feed_accounts(accounts)

    app_id = deploy(creator_pk=accounts[0][0])

    for i in range(0, 5):
        # Increase the counter's value three times and decrease 
        # it two times.
        if i < 3: 
            print("Counter's value increased by 1.")
            increase = True
        else:
            print("Counter's value decreased by 1.")
            increase = False

        modify_counter(
            account_pk=accounts[1][0],
            app_id=app_id,
            increase=increase
        )

    global_state = get_global_state(app_id)
    
    key = base64.b64encode("counter".encode()).decode()
    for item in global_state:
        if item["key"] == key:
            value = item["value"]
            print(f"Counter's value: {value['uint']}")
            break

if __name__ == "__main__":
    test()