from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer, 
    AccountTransactionSigner, 
    TransactionWithSigner
)
from algosdk.v2client import algod, indexer
from algosdk.future import transaction
from algosdk.abi import Contract
from algosdk import (
    account,
    error,
    logic
)
from pyteal import *

import base64


def deploy(
    algod_client: algod.AlgodClient,
    creator_pk  : str
) -> int:
    """
        Deploy the smart contract.

        Args:
            algod_client (algod.AlgodClient): algod client.
            creator_pk (str): smart contract's creator private key.

        Returns:
            (int): if successful, return the appilcation index of the
            deployed smart contract; otherwise, return -1.
    """
    with open("../../build/approval.teal", "r") as f: approval = f.read()
    with open("../../build/clear.teal"   , "r") as f: clear    = f.read()

    try:
        sender = account.address_from_private_key(creator_pk)

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


def propose_admin(
    algod_client       : algod.AlgodClient,
    admin_pk           : str,
    app_id             : int,
    admin_proposal_addr: str
) -> int:
    """
        Call smart contract method "propose_admin".

        Args:
            algod_client (algod.AlgodClient): algod client.
            admin_pk (str): administrator's private key.
            app_id (int): application index.
            admin_proposal_addr (str): proposed administrator address.

        Returns:
            (int): if successful, return the confirmation round; 
            otherwise, return -1.
    """
    try:
        sender = account.address_from_private_key(admin_pk)

        atc = AtomicTransactionComposer()

        signer = AccountTransactionSigner(admin_pk)

        suggested_parameters = algod_client.suggested_params()

        with open("./src/api.json") as f:
            js = f.read()
        c = Contract.from_json(js)

        atc.add_method_call(
            app_id=app_id,
            method=_get_method(c, "propose_admin"),
            sender=sender,
            sp=suggested_parameters,
            signer=signer,
            method_args=[admin_proposal_addr]
        )

        result = atc.execute(algod_client, 2)

        confirmation_round = result.confirmed_round

        return confirmation_round
    except error.AlgodHTTPError as e:
        print(e)
        return -1


def accept_admin_role(
    algod_client: algod.AlgodClient,
    new_admin_pk: str,
    app_id      : int
) -> int:
    """
        Call smart contract method "accept_admin_role".

        Args:
            algod_client (algod.AlgodClient): algod client.
            new_admin_pk (str): new administrator's private key.
            app_id (int): application index.

        Returns:
            (int): if successful, return the confirmation round; 
            otherwise, return -1.
    """
    try:
        sender = account.address_from_private_key(new_admin_pk)

        atc = AtomicTransactionComposer()

        signer = AccountTransactionSigner(new_admin_pk)

        suggested_parameters = algod_client.suggested_params()

        with open("./src/api.json") as f:
            js = f.read()
        c = Contract.from_json(js)

        atc.add_method_call(
            app_id=app_id,
            method=_get_method(c, "accept_admin_role"),
            sender=sender,
            sp=suggested_parameters,
            signer=signer
        )

        result = atc.execute(algod_client, 2)

        confirmation_round = result.confirmed_round

        return confirmation_round
    except error.AlgodHTTPError as e:
        print(e)
        return -1


def set_rate(
    algod_client    : algod.AlgodClient,
    admin_pk        : str, 
    app_id          : int,
    new_rate_integer: int, 
    new_rate_decimal: int
):
    """
        Call smart contract method "set_rate".

        Args:
            algod_client (algod.AlgodClient): algod client.
            admin_pk (str): administrator's private key.
            app_id (int): application index.
            new_rate_integer (int): integer part of the new swap rate.
            new_rate_decimal (int): number of decimals of the new swap rate.

        Returns:
            (int): if successful, return the confirmation round; 
            otherwise, return -1.
    """
    try:
        sender = account.address_from_private_key(admin_pk)

        atc = AtomicTransactionComposer()

        signer = AccountTransactionSigner(admin_pk)

        suggested_parameters = algod_client.suggested_params()

        with open("./src/api.json") as f:
            js = f.read()
        c = Contract.from_json(js)

        atc.add_method_call(
            app_id=app_id,
            method=_get_method(c, "set_rate"),
            sender=sender,
            sp=suggested_parameters,
            signer=signer,
            method_args=[new_rate_integer, new_rate_decimal]
        )

        result = atc.execute(algod_client, 2)

        confirmation_round = result.confirmed_round

        return confirmation_round
    except error.AlgodHTTPError as e:
        print(e)
        return -1


def optin_assets(
    algod_client : algod.AlgodClient,
    admin_pk     : str, 
    app_id       : int, 
    asset_id_from: int, 
    asset_id_to  : int
):
    """
        Call smart contract method "optin_assets".

        Args:
            algod_client (algod.AlgodClient): algod client.
            admin_pk (str): administrator's private key.
            app_id (int): application index.
            asset_id_from (int): source ASA's ID.
            asset_id_to (int): destination ASA's ID.

        Returns:
            (int): if successful, return the confirmation round; 
            otherwise, return -1.
    """
    try:
        sender = account.address_from_private_key(admin_pk)

        atc = AtomicTransactionComposer()

        signer = AccountTransactionSigner(admin_pk)

        suggested_parameters = algod_client.suggested_params()
        suggested_parameters.flat_fee = True
        suggested_parameters.fee = 1000

        with open("./src/api.json") as f:
            js = f.read()
        c = Contract.from_json(js)

        payment_txn = transaction.PaymentTxn(
            sender=sender,
            sp=suggested_parameters,
            receiver=logic.get_application_address(app_id),
            amt=200000
        )
        signed_payment_txn = TransactionWithSigner(payment_txn, signer)

        suggested_parameters.fee = 3000

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


def swap(
    algod_client  : algod.AlgodClient,
    account_pk    : str, 
    app_id        : int, 
    asset_id_from : int, 
    asset_id_to   : int, 
    amount_to_swap: int
):
    """
        Call smart contract method "swap".

        Args:
            algod_client (algod.AlgodClient): algod client.
            account_pk (str): account's private key.
            app_id (int): application index.
            asset_id_from (int): source ASA's ID.
            asset_id_to (int): destination ASA's ID.
            amount_to_swap (int): amount to swap.

        Returns:
            (int): if successful, return the confirmation round; 
            otherwise, return -1.
    """
    try:
        sender = account.address_from_private_key(account_pk)

        atc = AtomicTransactionComposer()

        signer = AccountTransactionSigner(account_pk)

        suggested_parameters = algod_client.suggested_params()
        suggested_parameters.flat_fee = True
        suggested_parameters.fee = 2000

        with open("./src/api.json") as f:
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

        suggested_parameters.fee = 1000
        
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


def create_asa(
    algod_client  : algod.AlgodClient,
    asa_creator_pk: str, 
    asa_manager_pk: str, 
    token_conf    : dict
):
    """
        Create ASA.

        Args:
            algod_client (algod.AlgodClient): algod client.
            asa_creator_pk (str): ASA creator's private key.
            asa_manager_pk (str): ASA manager's private key.
            token_conf (dict): token's configuration parameters.

        Returns:
            (int): if successful, return the asset's ID;
            otherwise, return -1.
    """
    try:
        creator = account.address_from_private_key(asa_creator_pk)
        manager = account.address_from_private_key(asa_manager_pk)

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
        signed_txn = unsigned_txn.sign(asa_creator_pk)

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


def optin_asa(
    algod_client: algod.AlgodClient,
    account_pk  : str, 
    asset_id    : int
):
    """
        Opt-in into ASA.

        Args:
            algod_client (algod.AlgodClient): algod client.
            account_pk (str): account's private key.
            asset_id (int): ASA's ID to opt-in.

        Returns:
            (int): if successful, return the confirmation round; 
            otherwise, return -1.
    """
    try:
        sender = account.address_from_private_key(account_pk)

        suggested_parameters = algod_client.suggested_params()

        unsigned_txn = transaction.AssetOptInTxn(
            sender=sender,
            sp=suggested_parameters,
            index=asset_id
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


def send_asa(
    algod_client : algod.AlgodClient,
    sender_pk    : str, 
    receiver_addr: str, 
    asset_id     : int, 
    amount       : int
):
    """
        Send ASA.

        Args:
            algod_client (algod.AlgodClient): algod client.
            sender_pk (str): senders's private key.
            receiver_addr (str): receiver's address.
            asset_id (int): ASA's ID to opt-in.
            amount (int): ASA amount to send.

        Returns:
            (int): if successful, return the confirmation round; 
            otherwise, return -1.
    """
    try:
        sender = account.address_from_private_key(sender_pk)

        suggested_parameters = algod_client.suggested_params()

        unsigned_txn = transaction.AssetTransferTxn(
            sender=sender,
            sp=suggested_parameters,
            receiver=receiver_addr,
            amt=amount,
            index=asset_id
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


def get_account_info(
    algod_client: algod.AlgodClient,
    account_addr: str
) -> dict:
    """
        Get account's info.

        Args:
            algod_client (algod.AlgodClient): algod client.
            account_pk (str): account's public key.

        Returns:
            (dict): account's info.
    """
    account_info = {}
    try:
        account_info = algod_client.account_info(account_addr)
    except error.AlgodHTTPError as e:
        print(e)
    finally:
        return account_info


def get_application_global_state(
    indexer_client: indexer.IndexerClient,
    app_id        : int
) -> dict:
    """
        Get application's global state.

        Args:
            indexer_client (indexer.IndexerClient): indexer client.
            app_id (int): application index.

        Returns:
            (dict): application's global state.
    """
    global_state = {}
    
    try:
        app = indexer_client.applications(app_id)

        for variable in app["application"]["params"]["global-state"]: 
            key   = variable["key"]
            value = variable["value"]

            key_decoded = base64.b64decode(key).decode()

            if value["type"] == 1:
                value_decoded = base64.b64decode(value["bytes"])
            else:
                value_decoded = value["uint"]

            print(key_decoded)
            print(value_decoded)

            global_state[key_decoded] = value_decoded
    except error.IndexerHTTPError as e:
        print(e)
    finally:
        return global_state


def get_asa_details(
    indexer_client: indexer.IndexerClient,
    asset_id: int
) -> dict:
    """
        Get asset information.

        Args:
            indexer_client (indexer.IndexerClient): indexer client.
            asset_id (int): asset id.

        Returns:
            (dict): asset information.
    """
    try:
        return indexer_client.asset_info(asset_id=asset_id)
    except error.IndexerHTTPError as e:
        print(e)
        return {}


def _get_method(
    contract: Contract, 
    name    : str
):
    """
        Get ABI method object from a contract.

        Args:
            contract (Contract): ABI contract description.
            name (str): method's name.

        Returns:
            (Method | None) ABI method object with initialized 
            arguments and return types or None in case the me-
            thod is not present in the contract.
    """
    for method in contract.methods:
        if method.name == name:
            return method
    return None


if __name__ == "__main__":
    pass
