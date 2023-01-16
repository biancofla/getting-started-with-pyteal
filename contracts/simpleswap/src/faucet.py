from algosdk.future import transaction
from algosdk.v2client import algod
from algosdk import (
    mnemonic,
    account,
    error
)


class Faucet:

    def __init__(self, passphrase):
        self.passphrase  = passphrase
        self.private_key = mnemonic.to_private_key(self.passphrase)


    def dispense(
        self,
        algod_client : algod.AlgodClient,
        receiver_addr: str,
        amount       : int
    ) -> int:
        """
            Dispense ALGOs.

            Args:
                algod_client (algod.AlgodClient): algod client.
                receiver (str): receiver's address.
                amount (int): amount to send.

            Returns:
                (int): if successful, return the confirmation round; 
                otherwise, return -1.
        """
        try:
            sender = account.address_from_private_key(self.private_key)
            print(sender)

            suggested_parameters = algod_client.suggested_params()

            unsigned_txn = transaction.PaymentTxn(
                sender=sender,
                sp=suggested_parameters,
                receiver=receiver_addr,
                amt=amount
            )
            signed_txn = unsigned_txn.sign(self.private_key)

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
