from pyteal import *

def handle_contract_creation():
    return Seq(

    )

router = Router(
    # Name of the contract.
    name="Simple Swap v0.1",
    # Handle bare call actions (transactions with 0 application arguments).
    bare_calls=BareCallActions(
        # On creation, simply approve the bare call.
        no_op=OnCompleteAction.always(Approve()),
        # On update/delete application, just reject the bare calls.
        update_application=OnCompleteAction.always(Reject()),
        delete_application=OnCompleteAction.always(Reject()),
        # The contract doesn't need a local state. Reject all the related
        # bare calls.
        close_out=OnCompleteAction.never(),
        opt_in=OnCompleteAction.never(),
        clear_state=OnCompleteAction.never()
    )
)