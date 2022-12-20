from algosdk.future import transaction
from algosdk.v2client import algod
from algosdk import (
    mnemonic,
    account,
    error
)

# Faucet configuration.
FAUCET_MNEMONIC    = "<FAUCET_MNEMONIC>"
FAUCET_PRIVATE_KEY = mnemonic.to_private_key(FAUCET_MNEMONIC)

algod_address = "http://localhost:4001"
algod_token   = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
algod_client  = algod.AlgodClient(
    algod_token=algod_token, 
    algod_address=algod_address
)


def fund_account(
    receiver: str, 
    amount  : int
) -> int:
    """
        Fund an account using a faucet account.

        Args:
            receiver (str): receiver's address.
            amount (int): amount to send.

        Returns:
            (int): if successful, return the confirmation round; 
            otherwise, return -1.
    """
    try:
        sender = account.address_from_private_key(FAUCET_PRIVATE_KEY)

        suggested_parameters = algod_client.suggested_params()

        unsigned_txn = transaction.PaymentTxn(
            sender=sender,
            sp=suggested_parameters,
            receiver=receiver,
            amt=amount
        )
        signed_txn = unsigned_txn.sign(FAUCET_PRIVATE_KEY)

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


if __name__ == "__main__":
    pass
