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
        amount=10000000
    )

    app_id = deploy(creator_pk=creator_pk)

    # Wait for indexer to catch-up newest algod updates.
    time.sleep(1)

    app_global_state = get_application_global_state(
        app_id=app_id
    )

    admin_addr = encoding.encode_address(app_global_state["admin"])
    
    assert admin_addr == creator_addr

def test_create_asa():
    pass

if __name__ == "__main__":
    pass