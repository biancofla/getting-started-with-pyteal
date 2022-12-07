from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer, 
    AccountTransactionSigner, 
    TransactionWithSigner
)
from algosdk.future import transaction
from algosdk.v2client import algod
from algosdk.abi import Contract
from algosdk import (
    account,
    error,
    logic
)
from pyteal import *

import base64
import os

# Sandbox configuration.
SANDBOX_COMMAND_PATH = "../../../sandbox/sandbox"
GENESIS_ADDRESS      = "S4Z25GO6DW6ZL6FKX5O3YFFVQEXAMMPZQOGO7VP3LHKRWJUJHKRF5WOM4M"
# Algod client configuration.
algod_address = "http://localhost:4001"
algod_token   = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
algod_client  = algod.AlgodClient(
    algod_token=algod_token, 
    algod_address=algod_address
)

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
        
        local_schema  = transaction.StateSchema(num_uints=0, num_byte_slices=0)
        global_schema = transaction.StateSchema(num_uints=3, num_byte_slices=0)

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

def optin_assets(account_pk, app_id, asset_id_from, asset_id_to):
    sender = account.address_from_private_key(account_pk)
    try:
        atc = AtomicTransactionComposer()

        signer = AccountTransactionSigner(account_pk)

        suggested_parameters = algod_client.suggested_params()

        with open("./api.json") as f:
            js = f.read()
        c = Contract.from_json(js)

        def get_method(name):
            for m in c.methods:
                if m.name == name:
                    return m
            raise(f"No method with the name {name}")

        atc.add_method_call(
            app_id=app_id,
            method=get_method("optin_assets"),
            sender=sender,
            sp=suggested_parameters,
            signer=signer,
            method_args=[asset_id_from, asset_id_to]
        )

        unsigned_txn = transaction.PaymentTxn(
            sender=sender,
            sp=suggested_parameters,
            receiver=logic.get_application_address(app_id),
            amt=100000
        )
        signed_txn = TransactionWithSigner(unsigned_txn, signer)
        atc.add_transaction(signed_txn)

        result = atc.execute(algod_client, 2)

        confirmation_round = result["confirmed-round"]

        return confirmation_round
    except error.AlgodHTTPError as e:
        print(e)
        return -1

if __name__ == "__main__":
    accounts = [account.generate_account() for _ in range(0, 2)]

    feed_accounts([a[1] for a in accounts])

    app_id = deploy(creator_pk=accounts[0][0])

    feed_accounts([logic.get_application_address(app_id)])

    # TODO: create ASAs.

    #cr = optin_assets(
    #    accounts[1][0],
    #    app_id,
    #    384303832,
    #    523683256
    #)