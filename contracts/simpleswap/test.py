from algosdk import (
    encoding,
    account
)

from contract_ops import *
from faucet import Faucet

import pytest
import time


@pytest.fixture(scope="session")
def algod_client():
    algod_address = "http://localhost:4001"
    algod_token   = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    algod_client  =  algod.AlgodClient(
        algod_token=algod_token, 
        algod_address=algod_address
    )   
    yield algod_client


@pytest.fixture(scope="session")
def indexer_client():
    indexer_address = "http://localhost:8980"
    indexer_token   = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    indexer_client  = indexer.IndexerClient(
        indexer_token=indexer_token,
        indexer_address=indexer_address
    )
    yield indexer_client


@pytest.fixture(scope="session")
def faucet():
    faucet = Faucet(
        passphrase="<FAUCET_PASSPHRASE>"
    )
    yield faucet


def test_deploy(algod_client, indexer_client, faucet):
    creator_pk, creator_addr = account.generate_account()

    faucet.dispense(
        algod_client=algod_client,
        receiver_addr=creator_addr, 
        # Total balance required is 415000 microAlgos:
        # * 100,000 is the minimum standard required balance;
        # * 100,000 is the per page creation application fee;
        # * (25,000 + 3,500 ) * 4 = 114,000 is the addition per integer entry;
        # * (25,000 + 25,000) * 2 = 50,000  is the addition per byte slice entry;
        # * 1000 is the transaction fee.
        amount=415_000
    )

    app_id = deploy(
        algod_client=algod_client,
        creator_pk=creator_pk
    )

    # Wait for indexer to catch-up newest algod updates.
    time.sleep(1)

    app_global_state = get_application_global_state(
        indexer_client=indexer_client,
        app_id=app_id
    )

    admin_addr = encoding.encode_address(app_global_state["admin"])
    
    assert admin_addr == creator_addr


def test_propose_admin(algod_client, indexer_client, faucet):
    admin_pk, admin_addr = account.generate_account()

    faucet.dispense(
        algod_client=algod_client,
        receiver_addr=admin_addr, 
        # Total balance required is 416000 microAlgos:
        # 1) 415000 microAlgos are required to deploy the smart-contract:
        #   * 100,000 is the minimum standard required balance;
        #   * 100,000 is the per page creation application fee;
        #   * (25,000 + 3,500 ) * 4 = 114,000 is the addition per integer entry;
        #   * (25,000 + 25,000) * 2 = 50,000  is the addition per byte slice entry;
        #   * 1000 is the transaction fee.
        # 2) 1000 microAlgos are the fee required to perform the smart-contract call 
        #    'propose_admin'.
        amount=416_000
    )

    app_id = deploy(
        algod_client=algod_client,
        creator_pk=admin_pk
    )

    new_admin_addr = account.generate_account()[1]

    propose_admin(
        algod_client=algod_client,
        admin_pk=admin_pk,
        app_id=app_id,
        admin_proposal_addr=new_admin_addr
    )

    # Wait for indexer to catch-up newest algod updates.
    time.sleep(1)
    
    app_global_state = get_application_global_state(
        indexer_client=indexer_client,
        app_id=app_id
    )

    app_admin_addr = encoding.encode_address(app_global_state["admin"])
    app_admin_proposal_addr = encoding.encode_address(app_global_state["admin-proposal"])

    assert (
        app_admin_proposal_addr == app_admin_proposal_addr and
        app_admin_addr          == admin_addr              
    )


def test_accept_admin_role(algod_client, indexer_client, faucet):
    admin_pk, admin_addr = account.generate_account()

    faucet.dispense(
        algod_client=algod_client,
        receiver_addr=admin_addr, 
        # Total balance required is 416000 microAlgos:
        # 1) 415000 microAlgos are required to deploy the smart-contract:
        #   * 100,000 is the minimum standard required balance;
        #   * 100,000 is the per page creation application fee;
        #   * (25,000 + 3,500 ) * 4 = 114,000 is the addition per integer entry;
        #   * (25,000 + 25,000) * 2 = 50,000  is the addition per byte slice entry;
        #   * 1000 is the transaction fee.
        # 2) 1000 microAlgos are the fee required to perform the smart-contract call 
        #    'propose_admin'.
        amount=416_000
    )

    app_id = deploy(
        algod_client=algod_client,
        creator_pk=admin_pk
    )

    new_admin_pk, new_admin_addr = account.generate_account()

    propose_admin(
        algod_client=algod_client,
        admin_pk=admin_pk,
        app_id=app_id,
        admin_proposal_addr=new_admin_addr
    )

    faucet.dispense(
        algod_client=algod_client,
        receiver_addr=new_admin_addr, 
        # Total balance required is 101000 microAlgos:
        # 1) 100,000 microAlgos is the minimum standard required balance;
        # 2) 1000 microAlgos are the fee required to perform the smart-contract call 
        #    'accept_admin_role'.
        amount=101_000
    )

    accept_admin_role(
        algod_client=algod_client,
        new_admin_pk=new_admin_pk,
        app_id=app_id
    )

    # Wait for indexer to catch-up newest algod updates.
    time.sleep(1)

    app_global_state = get_application_global_state(
        indexer_client=indexer_client,
        app_id=app_id
    )

    app_admin_addr = encoding.encode_address(app_global_state["admin"])
    app_admin_proposal_addr = app_global_state["admin-proposal"].decode()

    assert (
        app_admin_addr          == new_admin_addr and
        app_admin_proposal_addr == ""
    )


def test_set_rate(algod_client, indexer_client, faucet):
    admin_pk, admin_addr = account.generate_account()

    faucet.dispense(
        algod_client=algod_client,
        receiver_addr=admin_addr, 
        # Total balance required is 416000 microAlgos:
        # 1) 415000 microAlgos are required to deploy the smart-contract:
        #   * 100,000 is the minimum standard required balance;
        #   * 100,000 is the per page creation application fee;
        #   * (25,000 + 3,500 ) * 4 = 114,000 is the addition per integer entry;
        #   * (25,000 + 25,000) * 2 = 50,000  is the addition per byte slice entry;
        #   * 1000 is the transaction fee.
        # 2) 1000 microAlgos are the fee required to perform the smart-contract call 
        #    'set_rate'.
        amount=416_000
    )

    app_id = deploy(
        algod_client=algod_client,
        creator_pk=admin_pk
    )

    set_rate(
        algod_client=algod_client,
        admin_pk=admin_pk,
        app_id=app_id,
        new_rate_integer=5,
        new_rate_decimal=1
    )

    # Wait for indexer to catch-up newest algod updates.
    time.sleep(1)
    
    app_global_state = get_application_global_state(
        indexer_client=indexer_client,
        app_id=app_id
    )

    rate_integer = app_global_state["R"]
    rate_decimal = app_global_state["r"]

    assert rate_integer * (10 ** - rate_decimal) == 0.5


def test_optin_assets(algod_client, indexer_client, faucet):
    sm_creator_pk, sm_creator_addr = account.generate_account()

    faucet.dispense(
        algod_client=algod_client,
        receiver_addr=sm_creator_addr, 
        # Total balance required is 619000 microAlgos:
        # 1) 415000 microAlgos are required to deploy the smart-contract:
        #   * 100,000 is the minimum standard required balance;
        #   * 100,000 is the per page creation application fee;
        #   * (25,000 + 3,500 ) * 4 = 114,000 is the addition per integer entry;
        #   * (25,000 + 25,000) * 2 = 50,000  is the addition per byte slice entry;
        #   * 1000 is the transaction fees.
        # 2) 204000 microAlgos are required to perform the smart-contract call 
        #    'optin_assets':
        #   * 200,000 is the minimum amount of microAlgos that the smart 
        #     contract needs in order to handle two new ASAs;
        #   * 4000 are the transactions fees (one payment transaction 
        #     + no-op smart-contract call with two inner transactions).
        amount=619_000
    )

    app_id = deploy(
        algod_client=algod_client,
        creator_pk=sm_creator_pk
    )

    asa_creator_pk, asa_creator_addr = account.generate_account()
    asa_manager_pk                   = account.generate_account()[0]

    faucet.dispense(
        algod_client=algod_client,
        receiver_addr=asa_creator_addr, 
        # Total balance required is 302000 microAlgos:
        # * 100,000 is the minimum standard required balance;
        # * 200,000 is the minimum amount of microAlgos that the account 
        #   needs in order to handle two new ASAs;
        # * 2000 are the transactions fees needed to perform two ASAs
        #   creation operations.
        amount=302_000
    )

    token_a_conf = {
        "unit_name" : "Token A",
        "asset_name": "token-a",
        "total"     : 1_000_000_000,
        "decimals"  : 6
    }
    token_a_id = create_asa(
        algod_client=algod_client,
        asa_creator_pk=asa_creator_pk,
        asa_manager_pk=asa_manager_pk,
        token_conf=token_a_conf
    )
    token_b_conf = {
        "unit_name" : "Token B",
        "asset_name": "token-b",
        "total"     : 1_000_000_000,
        "decimals"  : 6
    }
    token_b_id = create_asa(
        algod_client=algod_client,
        asa_creator_pk=asa_creator_pk,
        asa_manager_pk=asa_manager_pk,
        token_conf=token_b_conf
    )
    
    faucet.dispense(
        algod_client=algod_client,
        receiver_addr=logic.get_application_address(app_id), 
        # Total balance required is 300000 microAlgos:
        # * 100,000 is the minimum standard required balance;
        # * 200,000 is the minimum amount of microAlgos that the account 
        #   needs in order to handle two new ASAs.
        amount=300_000
    )

    optin_assets(
        algod_client=algod_client,
        admin_pk=sm_creator_pk,
        app_id=app_id,
        asset_id_from=token_a_id,
        asset_id_to=token_b_id
    )

    # Wait for indexer to catch-up newest algod updates.
    time.sleep(1)

    app_global_state = get_application_global_state(
        indexer_client=indexer_client,
        app_id=app_id
    )

    admin_addr = encoding.encode_address(app_global_state["admin"])

    assert (
        app_global_state["asset-id-from"] == token_a_id and
        app_global_state["asset-id-to"]   == token_b_id and  
        sm_creator_addr                   == admin_addr
    )


def test_swap(algod_client, indexer_client, faucet):
    sm_creator_pk, sm_creator_addr = account.generate_account()

    faucet.dispense(
        algod_client=algod_client,
        receiver_addr=sm_creator_addr, 
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

    app_id = deploy(
        algod_client=algod_client,
        creator_pk=sm_creator_pk
    )

    asa_creator_pk, asa_creator_addr = account.generate_account()
    asa_manager_pk                   = account.generate_account()[0]

    faucet.dispense(
        algod_client=algod_client,
        receiver_addr=asa_creator_addr, 
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

    token_a_conf = {
        "unit_name" : "Token A",
        "asset_name": "token-a",
        "total"     : 1_000_000_000,
        "decimals"  : 6
    }
    token_a_id = create_asa(
        algod_client=algod_client,
        asa_creator_pk=asa_creator_pk,
        asa_manager_pk=asa_manager_pk,
        token_conf=token_a_conf
    )
    token_b_conf = {
        "unit_name" : "Token B",
        "asset_name": "token-b",
        "total"     : 1_000_000_000,
        "decimals"  : 6
    }
    token_b_id = create_asa(
        algod_client=algod_client,
        asa_creator_pk=asa_creator_pk,
        asa_manager_pk=asa_manager_pk,
        token_conf=token_b_conf
    )

    app_addr = logic.get_application_address(app_id)
    
    faucet.dispense(
        algod_client=algod_client,
        receiver_addr=app_addr, 
        # Total balance required is 300000 microAlgos:
        # * 100,000 is the minimum standard required balance;
        # * 200,000 is the minimum amount of microAlgos that the account 
        #   needs in order to handle two new ASAs.
        amount=300_000
    )

    optin_assets(
        algod_client=algod_client,
        admin_pk=sm_creator_pk,
        app_id=app_id,
        asset_id_from=token_a_id,
        asset_id_to=token_b_id
    )

    send_asa(
        algod_client=algod_client,
        sender_pk=asa_creator_pk,
        receiver_addr=app_addr,
        asset_id=token_a_id,
        amount=1_000_000
    )
    send_asa(
        algod_client=algod_client,
        sender_pk=asa_creator_pk,
        receiver_addr=app_addr,
        asset_id=token_b_id,
        amount=1_000_000
    )

    asa_user_pk, asa_user_addr = account.generate_account()

    faucet.dispense(
        algod_client=algod_client,
        receiver_addr=asa_user_addr, 
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

    optin_asa(
        algod_client=algod_client,
        account_pk=asa_user_pk,
        asset_id=token_a_id
    )
    optin_asa(
        algod_client=algod_client,
        account_pk=asa_user_pk,
        asset_id=token_b_id
    )

    send_asa(
        algod_client=algod_client,
        sender_pk=asa_creator_pk,
        receiver_addr=asa_user_addr,
        asset_id=token_a_id,
        amount=1_000_000
    )
    send_asa(
        algod_client=algod_client,
        sender_pk=asa_creator_pk,
        receiver_addr=asa_user_addr,
        asset_id=token_b_id,
        amount=1_000_000
    )

    set_rate(
        algod_client=algod_client,
        admin_pk=sm_creator_pk,
        app_id=app_id,
        new_rate_integer=5,
        new_rate_decimal=1
    )

    balances = {
        str(a["asset-id"]): a["amount"] 
        for a in get_account_info(algod_client, asa_user_addr)["assets"]
    }
    asset_a_balance_pre = balances[str(token_a_id)]
    asset_b_balance_pre = balances[str(token_b_id)]

    swap(
        algod_client=algod_client,
        account_pk=asa_user_pk,
        app_id=app_id,
        asset_id_from=token_a_id,
        asset_id_to=token_b_id,
        amount_to_swap=500_000
    )

    balances = {
        str(a["asset-id"]): a["amount"] 
        for a in get_account_info(algod_client, asa_user_addr)["assets"]
    }
    asset_a_balance_mid = balances[str(token_a_id)]
    asset_b_balance_mid = balances[str(token_b_id)]

    swap(
        algod_client=algod_client,
        account_pk=asa_user_pk,
        app_id=app_id,
        asset_id_from=token_b_id,
        asset_id_to=token_a_id,
        amount_to_swap=500_000
    )

    balances = {
        str(a["asset-id"]): a["amount"] 
        for a in get_account_info(algod_client, asa_user_addr)["assets"]
    }
    asset_a_balance_post = balances[str(token_a_id)]
    asset_b_balance_post = balances[str(token_b_id)]

    assert (
        asset_a_balance_pre  == 1_000_000 and 
        asset_b_balance_pre  == 1_000_000 and
        asset_a_balance_mid  ==   500_000 and 
        asset_b_balance_mid  == 1_250_000 and
        asset_a_balance_post == 1_500_000 and 
        asset_b_balance_post ==   750_000
    )


if __name__ == "__main__":
    pass
