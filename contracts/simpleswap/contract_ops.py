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

from faucet import fund_account

import base64

# Algod client configuration.
algod_address = "http://localhost:4001"
algod_token   = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
algod_client  = algod.AlgodClient(
    algod_token=algod_token, 
    algod_address=algod_address
)

def fund_accounts(
    accounts: list, 
    amount: int 
) -> None:
    """
        Fund the accounts.

        Args:
            accounts (list): accounts to feed.
    """
    for account in accounts: 
        fund_account(account, amount)

def deploy(
    creator_pk: str
) -> int:
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
        global_schema = transaction.StateSchema(num_uints=4, num_byte_slices=2)

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

def set_rate(
    creator_pk: str, 
    new_rate: int, 
    new_rate_decimals: int
):
    try:
        sender = account.address_from_private_key(creator_pk)

        atc = AtomicTransactionComposer()

        signer = AccountTransactionSigner(creator_pk)

        suggested_parameters = algod_client.suggested_params()

        with open("./api.json") as f:
            js = f.read()
        c = Contract.from_json(js)

        atc.add_method_call(
            app_id=app_id,
            method=_get_method(c, "set_rate"),
            sender=sender,
            sp=suggested_parameters,
            signer=signer,
            method_args=[new_rate, new_rate_decimals]
        )

        result = atc.execute(algod_client, 2)

        confirmation_round = result.confirmed_round

        return confirmation_round
    except error.AlgodHTTPError as e:
        print(e)
        return -1

def optin_assets(account_pk, app_id, asset_id_from, asset_id_to):
    sender = account.address_from_private_key(account_pk)
    try:
        atc = AtomicTransactionComposer()

        signer = AccountTransactionSigner(account_pk)

        suggested_parameters = algod_client.suggested_params()
        suggested_parameters.flat_fee = True
        suggested_parameters.fee = 3000

        with open("./api.json") as f:
            js = f.read()
        c = Contract.from_json(js)

        payment_txn = transaction.PaymentTxn(
            sender=sender,
            sp=suggested_parameters,
            receiver=logic.get_application_address(app_id),
            amt=200000
        )
        signed_payment_txn = TransactionWithSigner(payment_txn, signer)

        atc.add_method_call(
            app_id=app_id,
            method=_get_method(c, "optin_assets"),
            sender=sender,
            sp=suggested_parameters,
            signer=signer,
            method_args=[asset_id_from, asset_id_to, signed_payment_txn],
            foreign_assets=[asset_id_from, asset_id_to]
        )

        result = atc.execute(algod_client, 2)

        confirmation_round = result.confirmed_round

        return confirmation_round
    except error.AlgodHTTPError as e:
        print(e)
        return -1

def swap(account_pk, app_id, asset_id_from, asset_id_to, amount_to_swap):
    sender = account.address_from_private_key(account_pk)
    try:
        atc = AtomicTransactionComposer()

        signer = AccountTransactionSigner(account_pk)

        suggested_parameters = algod_client.suggested_params()
        suggested_parameters.flat_fee = True
        suggested_parameters.fee = 2000

        with open("./api.json") as f:
            js = f.read()
        c = Contract.from_json(js)

        asset_transfer_txn = transaction.AssetTransferTxn(
            sender=sender,
            sp=suggested_parameters,
            receiver=logic.get_application_address(app_id),
            amt=amount_to_swap,
            index=asset_id_from
        )
        asset_transfer_txn_signed = TransactionWithSigner(asset_transfer_txn, signer)

        atc.add_method_call(
            app_id=app_id,
            method=_get_method(c, "swap"),
            sender=sender,
            sp=suggested_parameters,
            signer=signer,
            method_args=[asset_transfer_txn_signed],
            foreign_assets=[asset_id_from, asset_id_to]
        )

        result = atc.execute(algod_client, 2)

        confirmation_round = result.confirmed_round

        return confirmation_round
    except error.AlgodHTTPError as e:
        print(e)
        return -1

def create_asa(creator_pk, manager_pk, token_conf):
    creator = account.address_from_private_key(creator_pk)
    manager = account.address_from_private_key(manager_pk)
    try:
        suggested_parameters = algod_client.suggested_params()

        unsigned_txn = transaction.AssetConfigTxn(
            sender=creator,
            sp=suggested_parameters,
            total=token_conf["total"],
            default_frozen=False,
            unit_name=token_conf["unit_name"],
            asset_name=token_conf["asset_name"],
            manager=manager,
            reserve=manager,
            freeze=manager,
            clawback=manager,
            decimals=token_conf["decimals"]
        )
        signed_txn = unsigned_txn.sign(creator_pk)

        txn_id = algod_client.send_transaction(signed_txn)

        result = transaction.wait_for_confirmation(
            algod_client=algod_client,
            txid=txn_id,
            wait_rounds=2
        )

        asset_id = result["asset-index"]

        return asset_id
    except error.AlgodHTTPError as e:
        print(e)
        return -1

def optin_asa(account_pk, asset_id_from):
    sender = account.address_from_private_key(account_pk)
    try:
        suggested_parameters = algod_client.suggested_params()

        unsigned_txn = transaction.AssetOptInTxn(
            sender=sender,
            sp=suggested_parameters,
            index=asset_id_from
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

def send_asa(sender_pk, receiver_addr, asset_id_from, amount):
    sender = account.address_from_private_key(sender_pk)
    try:
        suggested_parameters = algod_client.suggested_params()

        unsigned_txn = transaction.AssetTransferTxn(
            sender=sender,
            sp=suggested_parameters,
            receiver=receiver_addr,
            amt=amount,
            index=asset_id_from
        )
        signed_txn = unsigned_txn.sign(sender_pk)

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

def _get_method(c, name):
    for m in c.methods:
        if m.name == name:
            return m
    raise(f"No method with the name {name}")

if __name__ == "__main__":
    accounts = [account.generate_account() for _ in range(0, 4)]

    fund_accounts([a[1] for a in accounts], 10000000)

    app_id = deploy(creator_pk=accounts[0][0])

    fund_accounts([logic.get_application_address(app_id)], 100000)

    token_a_conf = {
        "unit_name" : "Token A",
        "asset_name": "token_a",
        "total"     : 1e9,
        "decimals"  : 6
    }
    token_a_id = create_asa(
        creator_pk=accounts[1][0],
        manager_pk=accounts[2][0],
        token_conf=token_a_conf
    )

    token_b_conf = {
        "unit_name" : "Token B",
        "asset_name": "token_b",
        "total"     : 1e9,
        "decimals"  : 6
    }
    token_b_id = create_asa(
        creator_pk=accounts[1][0],
        manager_pk=accounts[2][0],
        token_conf=token_b_conf
    )

    print("Opt-in Contract")
    cr_optin = optin_assets(
        accounts[0][0],
        app_id,
        token_a_id,
        token_b_id
    )

    print("Send Token A to swap program")
    cr_send_asa = send_asa(
        sender_pk=accounts[1][0],
        receiver_addr=logic.get_application_address(app_id),
        asset_id_from=token_a_id,
        amount=int(1e6)
    )
    print("Send Token B to swap program")
    cr_send_asa = send_asa(
        sender_pk=accounts[1][0],
        receiver_addr=logic.get_application_address(app_id),
        asset_id_from=token_b_id,
        amount=int(1e6)
    )

    print("Opt-in Token A")
    cr_optin_token_a = optin_asa(
        account_pk=accounts[3][0],
        asset_id_from=token_a_id
    )
    print("Opt-in Token B")
    cr_optin_token_a = optin_asa(
        account_pk=accounts[3][0],
        asset_id_from=token_b_id
    )

    print("Send Token A to account")
    cr_send_asa = send_asa(
        sender_pk=accounts[1][0],
        receiver_addr=accounts[3][1],
        asset_id_from=token_a_id,
        amount=1000000
    )
    print("Send Token B to account")
    cr_send_asa = send_asa(
        sender_pk=accounts[1][0],
        receiver_addr=accounts[3][1],
        asset_id_from=token_b_id,
        amount=1000000
    )

    print("Set conversion rate")
    cr_set_rate = set_rate(
        creator_pk=accounts[0][0],
        new_rate=5,
        new_rate_decimals=1
    )

    print("Swap Token A to Token B")
    cr_swap_1 = swap(
       account_pk=accounts[3][0],
       app_id=app_id,
       asset_id_from=token_a_id,
       asset_id_to=token_b_id,
       amount_to_swap=500000
    )
    print("Swap Token B to Token A")
    cr_swap_2 = swap(
       account_pk=accounts[3][0],
       app_id=app_id,
       asset_id_from=token_b_id,
       asset_id_to=token_a_id,
       amount_to_swap=500000
    )
