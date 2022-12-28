from algosdk import (
    encoding,
    account
)

from contract_ops import *

import time

def test_deploy():
    creator_pk, creator_addr = account.generate_account()

    fund_accounts(
        accounts=[creator_addr], 
        # Balance required is 415000:
        # * 100,000 is the minimum standard required balance;
        # * 100,000 is the per page creation application fee;
        # * (25,000 + 3,500 ) * 4 = 114,000 is the addition per integer entry;
        # * (25,000 + 25,000) * 2 = 50,000  is the addition per byte slice entry);
        # * 1000 is the transaction fee.
        amount=415000
    )

    app_id = deploy(creator_pk=creator_pk)

    # Wait for indexer to catch-up newest algod updates.
    time.sleep(1)

    app_global_state = get_application_global_state(app_id=app_id)

    admin_addr = encoding.encode_address(app_global_state["admin"])
    
    assert admin_addr == creator_addr


def test_create_asa():
    asa_creator_pk, asa_creator_addr = account.generate_account()
    asa_manager_pk, asa_manager_addr = account.generate_account()

    fund_accounts(
        accounts=[asa_creator_addr], 
        # Balance required is 201000:
        # * 100,000 is the minimum standard required balance;
        # * 100,000 is the fee associated with the creation of a new ASA;
        # * 1000 is the transaction fee.
        amount=201000
    )

    token_conf = {
        "unit_name" : "Token",
        "asset_name": "token",
        "total"     : 1e9,
        "decimals"  : 6
    }

    asset_id = create_asa(
        asa_creator_pk=asa_creator_pk,
        asa_manager_pk=asa_manager_pk,
        token_conf=token_conf
    )

    # Wait for indexer to catch-up newest algod updates.
    time.sleep(1)

    asa_params = get_asa_details(asset_id=asset_id)["asset"]["params"]

    assert (
        asa_params["creator"]   == asa_creator_addr         and
        asa_params["manager"]   == asa_manager_addr         and
        asa_params["unit-name"] == token_conf["unit_name"]  and
        asa_params["name"]      == token_conf["asset_name"] and
        asa_params["total"]     == token_conf["total"]      and
        asa_params["decimals"]  == token_conf["decimals"]
    )


def test_optin_assets():
    sm_creator_pk, sm_creator_addr = account.generate_account()

    fund_accounts(
        accounts=[sm_creator_addr], 
        # Balance required is 619000.
        # 1) 415000 are required to deploy contract:
        #   * 100,000 is the minimum standard required balance;
        #   * 100,000 is the per page creation application fee;
        #   * (25,000 + 3,500 ) * 4 = 114,000 is the addition per integer entry;
        #   * (25,000 + 25,000) * 2 = 50,000  is the addition per byte slice entry;
        #   * 1000 is the transaction fee.
        # 2) 204000 are required to perform contract opt-in operations:
        #   * 200,000 are the fees associated with the opt-in of two ASAs;
        #   * 4000 are the transactions fees (one payment transaction + no-op contract call with two inner transactions).
        amount=619000
    )

    app_id = deploy(creator_pk=sm_creator_pk)

    asa_creator_pk, asa_creator_addr = account.generate_account()
    asa_manager_pk, _ = account.generate_account()

    fund_accounts(
        accounts=[asa_creator_addr], 
        # Balance required is 302000:
        # * 100,000 is the minimum standard required balance;
        # * 100,000 * 2 = 200,000 are the fees associated with the creation of two new ASAs;
        # * 1000 * 2 = 2000 are the transactions fees.
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
        "unit_name" : "Token A",
        "asset_name": "token-a",
        "total"     : 1e9,
        "decimals"  : 6
    }
    token_b_id = create_asa(
        asa_creator_pk=asa_creator_pk,
        asa_manager_pk=asa_manager_pk,
        token_conf=token_b_conf
    )
    
    fund_accounts(
        accounts=[logic.get_application_address(app_id)], 
        # Balance required is 300000:
        # * 100,000 is the minimum standard required balance;
        # * 100,000 * 2 = 200,000 are the fees associated with the opt-in of two ASAs;
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
        admin_addr                        == sm_creator_addr and
        app_global_state["asset-id-from"] == token_a_id      and
        app_global_state["asset-id-to"]   == token_b_id 
    )


if __name__ == "__main__":
    pass