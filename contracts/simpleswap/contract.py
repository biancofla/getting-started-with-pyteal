from pyteal import *

global_admin         = Bytes("admin")
global_asset_id_from = Bytes("asset-id-from")
global_asset_id_to   = Bytes("asset-id-to")
global_rate          = Bytes("rate")

handle_creation = Seq(
    App.globalPut(global_admin, Txn.sender()),
    Approve()
)

router = Router(
    # Name of the contract.
    name="Simple Swap v0.1",
    # Handle bare call actions (i.e., transactions with 0 arguments).
    bare_calls=BareCallActions(
        # On creation, set admin address and approve transaction.
        no_op=OnCompleteAction.create_only(handle_creation),
        # The contract doesn't need a local state. There is no need
        # to handle the bare calls related to close out, opt-in and 
        # clear state.
        close_out=OnCompleteAction.never(),
        opt_in=OnCompleteAction.never(),
        clear_state=OnCompleteAction.never(),
        # On update/delete application, just reject the bare calls.
        update_application=OnCompleteAction.always(Reject()),
        delete_application=OnCompleteAction.always(Reject()),
    )
)

@router.method(no_op=CallConfig.CALL)
def get_admin(
    output: abi.Address
) -> Expr:
    """
        Lorem ipsum dolor sid amet.

        Returns:
            Lorem ipsum dolor sid amet.
    """
    return output.set(App.globalGet(global_admin))


@router.method(no_op=CallConfig.CALL)
def set_admin(
    new_admin_address: abi.String
) -> Expr:
    """
        Lorem ipsum dolor sid amet.

        Args:
            new_creator_address: Lorem ipsum dolor sid amet.
    """
    return Seq(
        Assert(
            And(
                # Check if the sender is the current administrator of the contract.
                Txn.sender()            == App.globalGet(global_admin),
                # Check if the new administator is not the current administrator of 
                # the contract. It will make no sense.
                new_admin_address.get() != App.globalGet(global_admin)
            )
        ),
        # Set 
        App.globalPut(global_admin, new_admin_address.get()),
        Approve()
    )


@router.method(no_op=CallConfig.CALL)
def get_rate(
    output: abi.Uint64
) -> Expr:
    """
        Lorem ipsum dolor sid amet.

        Returns:
            Lorem ipsum dolor sid amet.
    """
    return output.set(App.globalGet(global_rate))


@router.method(no_op=CallConfig.CALL)
def set_rate(
    new_rate: abi.Uint64
) -> Expr:
    """
        Lorem ipsum dolor sid amet.

        Args:
            new_rate: Lorem ipsum dolor sid amet.
    """
    return Seq(
        Assert(
            And(
                # Check if the sender is the current administrator of the contract.
                Txn.sender() == App.globalGet(global_admin),
                # Check if the new rate is greater than 0.
                new_rate.get() > Int(0)
            )
        ),
        # Set rate as global variable.
        App.globalPut(global_rate, new_rate.get()),
        Approve()
    )


@router.method(no_op=CallConfig.CALL)
def optin_assets(
    asset_id_from: abi.Uint64, 
    asset_id_to  : abi.Uint64
) -> Expr:
    """
        Lorem ipsum dolor sid amet.

        Args:
            asset_id_from: Lorem ipsum dolor sid amet.
            asset_id_to: Lorem ipsum dolor sid amet.
    """
    return Seq(
        Assert(
            And(
                *[
                    Gtxn[i].rekey_to() == Global.zero_address()
                    for i in range(2)
                ],
                # Check if the global variables are unset.
                App.globalGet(global_asset_id_from) == Int(0),
                App.globalGet(global_asset_id_to  ) == Int(0),
                # Check if the first transaction in the group:
                # 1) is a no-op application call;
                # 2) has the application id equal to the one of the current application.
                Gtxn[0].on_completion()      == OnComplete.NoOp,
                Gtxn[0].application_id()     == Global.current_application_id(),
                # Check if the second transaction in the group:
                # 1) is a payment transaction;
                # 2) has the payment's receiver address equal to the address of the application;
                # 3) has the close remainder address set to a zero address.
                Gtxn[1].type_enum()          == TxnType.Payment,
                Gtxn[1].receiver()           == Global.current_application_address(),
                Gtxn[1].close_remainder_to() == Global.zero_address()
            )
        ),
        # Opt-in into starting asset.
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields
        (
            {
                TxnField.type_enum     : TxnType.AssetTransfer,
                TxnField.xfer_asset    : asset_id_from.get(),
                TxnField.asset_receiver: Global.current_application_address(),
            }
        ),
        # Opt-in into destination asset.
        InnerTxnBuilder.Next(),
        InnerTxnBuilder.SetFields
        (
            {
                TxnField.type_enum     : TxnType.AssetTransfer,
                TxnField.xfer_asset    : asset_id_to.get(),
                TxnField.asset_receiver: Global.current_application_address(),
            }
        ),
        InnerTxnBuilder.Submit(),
        # Set source and destination asset global variables.
        App.globalPut(global_asset_id_from, asset_id_from.get()),
        App.globalPut(global_asset_id_to  , asset_id_to.get()  ),
        Approve()
    )


@router.method(no_op=CallConfig.CALL)
def swap() -> Expr:
    """
        Lorem ipsum dolor sid amet.
    """
    asset_to_transfer  = ScratchVar(TealType.uint64)
    amount_to_transfer = ScratchVar(TealType.uint64)

    return Seq(
        Assert(
            And(
                *[
                    Gtxn[i].rekey_to() == Global.zero_address()
                    for i in range(2)
                ],
                # Check if the first transaction in the group:
                # 1) is a no-op application call;
                # 2) has the application id equal to the one of the current application;
                # 3) has the number of arguments equal to zero.
                Gtxn[0].on_completion()  == OnComplete.NoOp,
                Gtxn[0].application_id() == Global.current_application_id(),
                # Check if the second transaction in the group:
                # 1) is an asset transfer transaction;
                # 2) has the asset to be transfered parameter equal 
                #    to the source/destination asset set as global variable;
                # 3) has the asset amount parameter greater than 0;
                # 4) has the sender address equal to the sender address of the 
                #    first transaction in the group;
                # 5) has the asset receiver address equal to the current application
                #    address.
                # 5) has the close remainder address set to a zero address;
                # 6) has the asset close address set to a zero address.
                Gtxn[1].type_enum()          == TxnType.AssetTransfer,
                Or(
                    Gtxn[1].xfer_asset() == App.globalGet(global_asset_id_from),
                    Gtxn[1].xfer_asset() == App.globalGet(global_asset_id_to  ),
                ),
                Gtxn[1].asset_amount()       >  Int(0),
                Gtxn[1].sender()             == Gtxn[0].sender(),
                Gtxn[1].asset_receiver()     == Global.current_application_address(),
                Gtxn[1].close_remainder_to() == Global.zero_address(),
                Gtxn[1].asset_close_to()     == Global.zero_address(),
            )
        ),
        # Check if:
        # 1)  the rate global variable is set;
        # 2a) in case the asset ID is equal to the source asset global variable,
        # check if the product between the asset amount and the rate global va-
        # riable doesn't overflow;
        # 2b) in case the asset ID is equal to the destination asset global va-
        # riable, store the result obtained from the division of the asset amount
        # and the rate.
        Assert(
            App.globalGet(global_rate) != Int(0)
        ),
        If(
            Gtxn[1].xfer_asset() == App.globalGet(global_asset_id_from),
        ).
        Then(
            Assert(
                Gtxn[1].asset_amount() * App.globalGet(global_rate) < Int(2 ** 64 - 1)
            ),
            asset_to_transfer.store(
                App.globalGet(global_asset_id_from)
            ),
            amount_to_transfer.store(
                Gtxn[1].asset_amount() * App.globalGet(global_rate)
            )
        ).
        Else(
            asset_to_transfer.store(
                App.globalGet(global_asset_id_to)
            ),
            amount_to_transfer.store(
                Gtxn[1].asset_amount() / App.globalGet(global_rate)
            )
        ),
        # Swap tokens.
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum     : TxnType.AssetTransfer,
                TxnField.asset_receiver: Txn.sender(),
                TxnField.xfer_asset    : asset_to_transfer.load(),
                TxnField.asset_amount  : amount_to_transfer.load()
            }
        ),
        InnerTxnBuilder.Submit(),
        Approve()
    )
    

if __name__ == "__main__":
    import json 

    approval_program, clear_state_program, contract = router.compile_program(
        version=6, 
        optimize=OptimizeOptions(scratch_slots=True)
    )

    with open("../../build/approval.teal", "w") as f:
        f.write(approval_program)

    with open("../../build/clear.teal", "w") as f:
        f.write(clear_state_program)

    with open("api.json", "w") as f:
        f.write(
            json.dumps(
                contract.dictify(), 
                indent=4
            )
        )
