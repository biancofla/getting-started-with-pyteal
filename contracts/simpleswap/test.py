from algosdk import (
    encoding,
    account
)

from contract_ops import *
from faucet import Faucet

import pytest
import time


@pytest.fixture(scope="session")
def faucet():
    faucet = Faucet(
        passphrase="<FAUCET_PASSPHRASE>"
    )
    yield faucet


def test_deploy(faucet):
    creator_pk, creator_addr = account.generate_account()

    faucet.dispense(
        receiver_addr=creator_addr, 
        # 415000 microAlgos are required in order to deploy the smart-contract:
        # * 100,000 is the minimum standard required balance;
        # * 100,000 is the per page creation application fee;
        # * (25,000 + 3,500 ) * 4 = 114,000 is the addition per integer entry;
        # * (25,000 + 25,000) * 2 = 50,000  is the addition per byte slice entry;
        # * 1000 is the transaction fee.
        amount=415000
    )

    app_id = deploy(creator_pk=creator_pk)

    # Wait for indexer to catch-up newest algod updates.
    time.sleep(1)

    app_global_state = get_application_global_state(app_id=app_id)

    admin_addr = encoding.encode_address(app_global_state["admin"])
    
    assert admin_addr == creator_addr


def test_propose_admin(faucet):
    admin_pk, admin_addr = account.generate_account()

    faucet.dispense(
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
        amount=416000
    )

    app_id = deploy(creator_pk=admin_pk)

    new_admin_addr = account.generate_account()[1]

    propose_admin(
        admin_pk=admin_pk,
        app_id=app_id,
        admin_proposal_addr=new_admin_addr
    )

    # Wait for indexer to catch-up newest algod updates.
    time.sleep(1)
    
    app_global_state = get_application_global_state(app_id=app_id)

    app_admin_addr = encoding.encode_address(app_global_state["admin"])
    app_admin_proposal_addr = encoding.encode_address(app_global_state["admin-proposal"])

    assert (
        app_admin_proposal_addr == app_admin_proposal_addr and
        app_admin_addr          == admin_addr              
    )


def test_accept_admin_role(faucet):
    admin_pk, admin_addr = account.generate_account()

    faucet.dispense(
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
        amount=416000
    )

    app_id = deploy(creator_pk=admin_pk)

    new_admin_pk, new_admin_addr = account.generate_account()

    propose_admin(
        admin_pk=admin_pk,
        app_id=app_id,
        admin_proposal_addr=new_admin_addr
    )

    faucet.dispense(
        receiver_addr=new_admin_addr, 
        # Total balance required is 416000 microAlgos:
        # 1) 415000 microAlgos are required to deploy the smart-contract:
        #   * 100,000 is the minimum standard required balance;
        #   * 100,000 is the per page creation application fee;
        #   * (25,000 + 3,500 ) * 4 = 114,000 is the addition per integer entry;
        #   * (25,000 + 25,000) * 2 = 50,000  is the addition per byte slice entry;
        #   * 1000 is the transaction fee.
        # 2) 1000 microAlgos are the fee required to perform the smart-contract call 
        #    'accept_admin_role'.
        amount=101000
    )

    accept_admin_role(
        new_admin_pk=new_admin_pk,
        app_id=app_id
    )

    # Wait for indexer to catch-up newest algod updates.
    time.sleep(1)

    app_global_state = get_application_global_state(app_id=app_id)

    app_admin_addr = encoding.encode_address(app_global_state["admin"])
    app_admin_proposal_addr = app_global_state["admin-proposal"].decode()

    assert (
        app_admin_addr          == new_admin_addr and
        app_admin_proposal_addr == ""
    )


def test_set_rate(faucet):
    admin_pk, admin_addr = account.generate_account()

    faucet.dispense(
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
        amount=416000
    )

    app_id = deploy(creator_pk=admin_pk)

    set_rate(
        admin_pk=admin_pk,
        app_id=app_id,
        new_rate_integer=5,
        new_rate_decimal=1
    )

    # Wait for indexer to catch-up newest algod updates.
    time.sleep(1)
    
    app_global_state = get_application_global_state(app_id=app_id)

    rate_integer = app_global_state["R"]
    rate_decimal = app_global_state["r"]

    assert rate_integer * (10 ** - rate_decimal) == 0.5


def test_optin_assets(faucet):
    sm_creator_pk, sm_creator_addr = account.generate_account()

    faucet.dispense(
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
        amount=619000
    )

    app_id = deploy(creator_pk=sm_creator_pk)

    asa_creator_pk, asa_creator_addr = account.generate_account()
    asa_manager_pk                   = account.generate_account()[0]

    faucet.dispense(
        receiver_addr=asa_creator_addr, 
        # Total balance required is 302000 microAlgos:
        # * 100,000 is the minimum standard required balance;
        # * 200,000 is the minimum amount of microAlgos that the account 
        #   needs in order to handle two new ASAs;
        # * 2000 are the transactions fees needed to perform two ASAs
        #   creation operations.
        amount=302000
    )

    token_a_conf = {
        "unit_name" : "Token A",
        "asset_name": "token-a",
        "total"     : 1e9,
        "decimals"  : 6
    }
    token_a_id = create_asa(
        asa_creator_pk=asa_creator_pk,
        asa_manager_pk=asa_manager_pk,
        token_conf=token_a_conf
    )
    token_b_conf = {
        "unit_name" : "Token B",
        "asset_name": "token-b",
        "total"     : 1e9,
        "decimals"  : 6
    }
    token_b_id = create_asa(
        asa_creator_pk=asa_creator_pk,
        asa_manager_pk=asa_manager_pk,
        token_conf=token_b_conf
    )
    
    faucet.dispense(
        receiver_addr=logic.get_application_address(app_id), 
        # Total balance required is 300000 microAlgos:
        # * 100,000 is the minimum standard required balance;
        # * 200,000 is the minimum amount of microAlgos that the account 
        #   needs in order to handle two new ASAs.
        amount=300000
    )

    optin_assets(
        admin_pk=sm_creator_pk,
        app_id=app_id,
        asset_id_from=token_a_id,
        asset_id_to=token_b_id
    )

    # Wait for indexer to catch-up newest algod updates.
    time.sleep(1)

    app_global_state = get_application_global_state(app_id=app_id)

    admin_addr = encoding.encode_address(app_global_state["admin"])

    assert (
        app_global_state["asset-id-from"] == token_a_id and
        app_global_state["asset-id-to"]   == token_b_id and  
        sm_creator_addr                   == admin_addr
    )


def test_swap(faucet):
    sm_creator_pk, sm_creator_addr = account.generate_account()

    faucet.dispense(
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
        amount=620000
    )

    app_id = deploy(creator_pk=sm_creator_pk)

    asa_creator_pk, asa_creator_addr = account.generate_account()
    asa_manager_pk                   = account.generate_account()[0]

    faucet.dispense(
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
        amount=306000
    )

    token_a_conf = {
        "unit_name" : "Token A",
        "asset_name": "token-a",
        "total"     : 1e9,
        "decimals"  : 6
    }
    token_a_id = create_asa(
        asa_creator_pk=asa_creator_pk,
        asa_manager_pk=asa_manager_pk,
        token_conf=token_a_conf
    )
    token_b_conf = {
        "unit_name" : "Token B",
        "asset_name": "token-b",
        "total"     : 1e9,
        "decimals"  : 6
    }
    token_b_id = create_asa(
        asa_creator_pk=asa_creator_pk,
        asa_manager_pk=asa_manager_pk,
        token_conf=token_b_conf
    )

    app_addr = logic.get_application_address(app_id)
    
    faucet.dispense(
        receiver_addr=app_addr, 
        # Total balance required is 300000 microAlgos:
        # * 100,000 is the minimum standard required balance;
        # * 200,000 is the minimum amount of microAlgos that the account 
        #   needs in order to handle two new ASAs.
        amount=300000
    )

    optin_assets(
        admin_pk=sm_creator_pk,
        app_id=app_id,
        asset_id_from=token_a_id,
        asset_id_to=token_b_id
    )

    send_asa(
        sender_pk=asa_creator_pk,
        receiver_addr=app_addr,
        asset_id=token_a_id,
        amount=int(1e6)
    )
    send_asa(
        sender_pk=asa_creator_pk,
        receiver_addr=app_addr,
        asset_id=token_b_id,
        amount=int(1e6)
    )

    asa_user_pk, asa_user_addr = account.generate_account()

    faucet.dispense(
        receiver_addr=asa_user_addr, 
        # Total balance required is 308000 microAlgos:
        # 1) 300000 microAlgos are required in order to handle two ASAs:
        #   * 100,000 is the minimum standard required balance;
        #   * 200,000 is the minimum amount of microAlgos that the account 
        #     needs in order to handle two new ASAs.
        #   8 2000 are the fee needed to perform two opt-in operations.
        # 2) 8000 are the fee required to perform two smart-contract calls 
        #    to the 'swap' method (3000 microAlgos per call).
        amount=308000
    )

    optin_asa(
        account_pk=asa_user_pk,
        asset_id=token_a_id
    )
    optin_asa(
        account_pk=asa_user_pk,
        asset_id=token_b_id
    )

    send_asa(
        sender_pk=asa_creator_pk,
        receiver_addr=asa_user_addr,
        asset_id=token_a_id,
        amount=int(1e6)
    )
    send_asa(
        sender_pk=asa_creator_pk,
        receiver_addr=asa_user_addr,
        asset_id=token_b_id,
        amount=int(1e6)
    )

    set_rate(
        admin_pk=sm_creator_pk,
        app_id=app_id,
        new_rate_integer=5,
        new_rate_decimal=1
    )

    balances = {
        str(a["asset-id"]): a["amount"] 
        for a in get_account_info(asa_user_addr)["assets"]
    }
    asset_a_balance_pre = balances[str(token_a_id)]
    asset_b_balance_pre = balances[str(token_b_id)]

    swap(
        account_pk=asa_user_pk,
        app_id=app_id,
        asset_id_from=token_a_id,
        asset_id_to=token_b_id,
        amount_to_swap=int(5e5)
    )

    balances = {
        str(a["asset-id"]): a["amount"] 
        for a in get_account_info(asa_user_addr)["assets"]
    }
    asset_a_balance_mid = balances[str(token_a_id)]
    asset_b_balance_mid = balances[str(token_b_id)]

    swap(
        account_pk=asa_user_pk,
        app_id=app_id,
        asset_id_from=token_b_id,
        asset_id_to=token_a_id,
        amount_to_swap=int(5e5)
    )

    balances = {
        str(a["asset-id"]): a["amount"] 
        for a in get_account_info(asa_user_addr)["assets"]
    }
    asset_a_balance_post = balances[str(token_a_id)]
    asset_b_balance_post = balances[str(token_b_id)]

    assert (
        asset_a_balance_pre  == 1000000 and 
        asset_b_balance_pre  == 1000000 and
        asset_a_balance_mid  ==  500000 and 
        asset_b_balance_mid  == 1250000 and
        asset_a_balance_post == 1500000 and 
        asset_b_balance_post ==  750000
    )


if __name__ == "__main__":
    pass