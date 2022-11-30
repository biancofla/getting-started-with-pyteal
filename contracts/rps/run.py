from algosdk.future import transaction
from algosdk.v2client import algod
from algosdk import (
    account,
    error,
    logic
)
from pyteal import *

import hashlib
import base64
import json
import os

SANDBOX_COMMAND_PATH = "../../../sandbox/sandbox"
GENESIS_ADDRESS      = "S4Z25GO6DW6ZL6FKX5O3YFFVQEXAMMPZQOGO7VP3LHKRWJUJHKRF5WOM4M"

CHALLENGER_REVEAL = "p"
OPPONENT_REVEAL   = "p"

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
            f"{SANDBOX_COMMAND_PATH} goal clerk send -f {GENESIS_ADDRESS} -t {account} -a 1000000"
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
    """
        Perform opt-in operation.

        Args:
            * account_pk (str): opt-in account's private key.
            * app_id (int): application index.

        Returns:
            * (int): if successful, return the confirmation round; 
            otherwise, return -1.
    """
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

def create_challenge(challenger_pk, commitment, app_id, opponent_addr):
    """
        Create challenge.

        Args:
            * challenger_pk (str): challenger's private key.
            * commitment (str): challenger's commitment.
            * app_id (int): application index.
            * opponent_addr (str): opponent's address.

        Returns:
            * (int): if successful, return the confirmation round; 
            otherwise, return -1.
    """
    sender = account.address_from_private_key(challenger_pk)
    try:
        suggested_parameters = algod_client.suggested_params()

        app_args = []
        app_args.append("challenge".encode())
        app_args.append(
            hashlib.sha256(commitment.encode("utf-8")).digest()
        )

        unsigned_txn_1 = transaction.ApplicationNoOpTxn(
            sender=sender,
            sp=suggested_parameters,
            index=app_id,
            app_args=app_args,
            accounts=[opponent_addr]
        )
        unsigned_txn_2 = transaction.PaymentTxn(
            sender=sender,
            sp=suggested_parameters,
            receiver=logic.get_application_address(app_id),
            amt=123456
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
            txid=txn_id,
            wait_rounds=4
        )

        confirmation_round = result["confirmed-round"]

        return confirmation_round
    except error.AlgodHTTPError as e:
        print(e)
        return -1

def accept_challenge(opponent_pk, opponent_reveal, app_id, challenger_addr):
    """
        Accept challenge.

        Args:
            * opponent_pk (str): opponent's private key.
            * opponent_reveal (str): opponent's reveal.
            * app_id (int): application index.
            * challenger_addr (str): challenger's address.

        Returns:
            * (int): if successful, return the confirmation round; 
            otherwise, return -1.
    """
    sender = account.address_from_private_key(opponent_pk)
    try:
        suggested_parameters = algod_client.suggested_params()

        app_args = []
        app_args.append("accept".encode())
        app_args.append(opponent_reveal.encode())

        unsigned_txn_1 = transaction.ApplicationNoOpTxn(
            sender=sender,
            sp=suggested_parameters,
            index=app_id,
            app_args=app_args,
            accounts=[challenger_addr]
        )
        unsigned_txn_2 = transaction.PaymentTxn(
            sender=sender,
            sp=suggested_parameters,
            receiver=logic.get_application_address(app_id),
            amt=123456
        )

        group_id = transaction.calculate_group_id(
            [unsigned_txn_1, unsigned_txn_2]
        )
        unsigned_txn_1.group = group_id
        unsigned_txn_2.group = group_id

        signed_txn_1 = unsigned_txn_1.sign(opponent_pk)
        signed_txn_2 = unsigned_txn_2.sign(opponent_pk)

        signed_group = [signed_txn_1, signed_txn_2]

        txn_id = algod_client.send_transactions(signed_group)

        result = transaction.wait_for_confirmation(
            algod_client=algod_client,
            txid=txn_id,
            wait_rounds=4
        )

        confirmation_round = result["confirmed-round"]

        return confirmation_round
    except error.AlgodHTTPError as e:
        print(e)
        return -1

def reveal(challenger_pk, challenger_reveal, app_id, opponent_addr):
    """
        Do the reveal operation.

        Args:
            * challenger_pk (str): challenger's private key.
            * challenger_reveal (str): challenger's reveal.
            * app_id (int): application index.
            * opponent_addr (str): opponent's address.

        Returns:
            * (int): if successful, return the confirmation round; 
            otherwise, return -1.
    """
    sender = account.address_from_private_key(challenger_pk)
    try:
        suggested_parameters = algod_client.suggested_params()
        suggested_parameters.flat_fee = True
        suggested_parameters.fee = 3000

        app_args = []
        app_args.append("reveal".encode())
        app_args.append(challenger_reveal.encode())

        unsigned_txn = transaction.ApplicationNoOpTxn(
            sender=sender,
            sp=suggested_parameters,
            index=app_id,
            app_args=app_args,
            accounts=[opponent_addr]
        )
        signed_txn = unsigned_txn.sign(challenger_pk)

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

def get_local_state(address, app_id):
    """
        Get application's local state.

        Args:
            * address (str): account's address.
            * app_id (int): application index.

        Returns:
            (dict): application's local state.
    """
    formatted_local_state = {}
    try:
        account_info = algod_client.account_info(address)
        for app_local_state in account_info["apps-local-state"]:
            if app_local_state["id"] == app_id:
                local_state = app_local_state["key-value"]
                for ls in local_state:
                    k, v_dict = ls["key"], ls["value"]
                    if v_dict["type"] == 1: 
                        v = v_dict["bytes"]
                    else: 
                        v = v_dict["uint"]
                    k = base64.b64decode(k).decode()
                    formatted_local_state[k] = v
    except error.AlgodHTTPError as e:
        print(e)
    finally:
        return formatted_local_state

def test():
    accounts = [account.generate_account() for _ in range(0, 3)]

    feed_accounts([a[1] for a in accounts])

    app_id = deploy(creator_pk=accounts[0][0])

    feed_accounts([logic.get_application_address(app_id)])
    
    print("Opting in accounts...")
    optin_account_1 = optin(accounts[1][0], app_id)
    optin_account_2 = optin(accounts[2][0], app_id)
    if optin_account_1 > -1 and optin_account_2 > -1:
        print(f"{accounts[1][1]} local state:")
        print(
            json.dumps(
                get_local_state(accounts[1][1], app_id),
                indent=4
            )
        )
        print(f"{accounts[2][1]} local state:")
        print(
            json.dumps(
                get_local_state(accounts[2][1], app_id),
                indent=4
            )
        )
        
        print("Creating challenge...")
        create_challenge_cr = create_challenge(
            accounts[1][0],
            CHALLENGER_REVEAL,
            app_id,
            accounts[2][1]
        )
        if create_challenge_cr > -1:
            print("Accepting challenge...")
            accept_challenge_cr = accept_challenge(
                accounts[2][0],
                OPPONENT_REVEAL,
                app_id,
                accounts[1][1]
            )
            if accept_challenge_cr > -1:
                print(f"{accounts[1][1]} local state:")
                print(
                    json.dumps(
                        get_local_state(accounts[1][1], app_id),
                        indent=4
                    )
                )
                print(f"{accounts[2][1]} local state:")
                print(
                    json.dumps(
                        get_local_state(accounts[2][1], app_id),
                        indent=4
                    )
                )
                
                print("Revealing...")
                reveal_cr = reveal(
                    accounts[1][0],
                    CHALLENGER_REVEAL,
                    app_id,
                    accounts[2][1]
                )
                if reveal_cr > -1:
                    print(
                        f"{accounts[1][1]} balance: {algod_client.account_info(accounts[1][1])['amount']} MicroAlgos"
                    )
                    print(
                        f"{accounts[2][1]} balance: {algod_client.account_info(accounts[2][1])['amount']} MicroAlgos"
                    )

if __name__ == "__main__":
    test()