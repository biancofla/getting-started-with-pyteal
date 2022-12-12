from pyteal import *

global_asset_id_from = Bytes("asset-id-from")
global_asset_id_to   = Bytes("asset-id-to")
global_multiplier    = Bytes("multiplier")

asset_decimal = AssetParam.decimals(
    App.globalGet(global_asset_id_to)
)

router = Router(
    # Name of the contract.
    name="Simple Swap v0.1",
    # Handle bare call actions (i.e., transactions with 0 arguments).
    bare_calls=BareCallActions(
        # On creation, simply approve the bare call.
        no_op=OnCompleteAction.create_only(Approve()),
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
                Global.group_size() == Int(2),
                Txn.group_index()   == Int(0),
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
        Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields
            (
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.xfer_asset: asset_id_from.get(),
                    TxnField.asset_receiver: Global.current_application_address(),
                }
            ),
            InnerTxnBuilder.Submit(),
        ),
        # Opt-in into destination asset.
        Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields
            (
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.xfer_asset: asset_id_to.get(),
                    TxnField.asset_receiver: Global.current_application_address(),
                }
            ),
            InnerTxnBuilder.Submit(),
        ),
        # Set source and destination asset global variables.
        App.globalPut(global_asset_id_from, asset_id_from.get()),
        App.globalPut(global_asset_id_to  , asset_id_to.get()  ),
        # Get the number of decimals for a specific asset.
        asset_decimal,
        Assert(
            # Throw an error if the asset doesn't exists.
            asset_decimal.hasValue()
        ),
        # Set the multiplier global variable.
        App.globalPut(global_multiplier, Exp(Int(10), asset_decimal.value())),
        Approve()
    )

@router.method(no_op=CallConfig.CALL)
def swap() -> Expr:
    """
        Lorem ipsum dolor sid amet.
    """
    return Seq(
        Assert(
            And(
                Global.group_size() == Int(3),
                Txn.group_index()   == Int(0),
                *[
                    Gtxn[i].rekey_to() == Global.zero_address()
                    for i in range(3)
                ],
                # Check if the first transaction in the group:
                # 1) is a no-op application call;
                # 2) has the application id equal to the one of the current application;
                # 3) has the number of arguments equal to zero.
                Gtxn[0].on_completion()           == OnComplete.NoOp,
                Gtxn[0].application_id()          == Global.current_application_id(),
                Gtxn[0].application_args.length() == Int(0),
                # Check if the second transaction in the group:
                # 1) is an asset transfer transaction;
                # 2) has the asset to be transfered parameter equal 
                #    to the destination asset set as global variable;
                # 3) has the asset amount parameter set to 0;
                # 4) has the sender address equal to the asset receiver address;
                # 5) has the rekey address set to a zero address;
                # 6) has the close remainder address set to a zero address;
                # 7) has the asset close address set to a zero address.
                Gtxn[1].type_enum()          == TxnType.AssetTransfer,
                Gtxn[1].xfer_asset()         == App.globalGet(global_asset_id_to),
                Gtxn[1].asset_amount()       == Int(0),
                Gtxn[1].sender()             == Gtxn[1].asset_receiver(),
                Gtxn[1].rekey_to()           == Global.zero_address(),
                Gtxn[1].close_remainder_to() == Global.zero_address(),
                Gtxn[1].asset_close_to()     == Global.zero_address(),
                # Check if the third transaction in the group:
                # 1) is an asset transfer transaction;
                # 2) has the asset to be transfered parameter equal 
                #    to the source asset set as global variable;
                # 3) has the asset amount parameter greater than 0;
                # 4) has the sender address equal to the sender address of the 
                #    first transaction in the group;
                # 5) has the rekey address set to a zero address;
                # 6) has the close remainder address set to a zero address;
                # 7) has the asset close address set to a zero address.
                Gtxn[2].type_enum()          == TxnType.AssetTransfer,
                Gtxn[2].xfer_asset()         == App.globalGet(global_asset_id_from),
                Gtxn[2].asset_amount()       >  Int(0),
                Gtxn[2].sender()             == Gtxn[1].sender(),
                Gtxn[2].receiver()           == Global.current_application_address(),
                Gtxn[2].rekey_to()           == Global.zero_address(),
                Gtxn[2].close_remainder_to() == Global.zero_address(),
                Gtxn[2].asset_close_to()     == Global.zero_address(),
            )
        ),
        # Swap source token into destination token.
        Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.asset_receiver: Txn.sender(),
                    TxnField.asset_amount: Gtxn[2].asset_amount() * App.globalGet(global_multiplier),
                    TxnField.xfer_asset: App.globalGet(global_asset_id_to),
                }
            ),
            InnerTxnBuilder.Submit(),
        ),
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
