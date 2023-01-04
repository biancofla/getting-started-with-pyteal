from pyteal import *

global_admin          = Bytes("admin")
global_admin_proposal = Bytes("admin-proposal")
global_asset_id_from  = Bytes("asset-id-from")
global_asset_id_to    = Bytes("asset-id-to")
global_rate_integer   = Bytes("R")
global_rate_decimal   = Bytes("r")

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
        delete_application=OnCompleteAction.always(Reject())
    )
)


@router.method(no_op=CallConfig.CALL)
def propose_admin(
    new_admin_address: abi.Address
) -> Expr:
    """
        Propose a new administrator.

        Args:
            new_creator_address: Address of the proposed administrator.
    """
    return Seq(
        Assert(
            # Check if the sender is the current administrator.
            Txn.sender() == App.globalGet(global_admin),
        ),
        App.globalPut(global_admin_proposal, new_admin_address.get())
    )


@router.method(no_op=CallConfig.CALL)
def accept_admin_role() -> Expr:
    """
        Accept the administrator's role.
    """
    return Seq(
        Assert(
            # Check if the sender is the current proposed administrator.
            App.globalGet(global_admin_proposal) == Txn.sender()
        ),
        # Set new administrator address.
        App.globalPut(global_admin, App.globalGet(global_admin_proposal)),
        # Reset administrator proposal address.
        App.globalPut(global_admin_proposal, Bytes(""))
    )


@router.method(no_op=CallConfig.CALL)
def set_rate(
    new_rate_integer: abi.Uint64,
    new_rate_decimal: abi.Uint64
) -> Expr:
    """
        Set swap rate.

        Args:
            new_rate_integer: integer part of the new swap rate.
            new_rate_decimal: number of decimals of the new swap rate.
    """
    return Seq(
        Assert(
            And(
                # Check if the sender is the current administrator of
                # the contract.
                Txn.sender() == App.globalGet(global_admin),
                # Check if the new rate is greater than 0.
                new_rate_integer.get() > Int(0)
            )
        ),
        # Set new rate.
        App.globalPut(global_rate_integer, new_rate_integer.get()),
        # Set new rate decimals.
        App.globalPut(global_rate_decimal, new_rate_decimal.get()),
        Approve()
    )


@router.method(no_op=CallConfig.CALL)
def optin_assets(
    asset_id_from: abi.Uint64, 
    asset_id_to  : abi.Uint64,
    txn          : abi.PaymentTransaction
) -> Expr:
    """
        Opt-in assets.

        Args:
            asset_id_from: source asset.
            asset_id_to: destination asset.
            txn: payment transaction.
    """
    return Seq(
        Assert(
            And(
                # Check if the source/destination asset are unset.
                App.globalGet(global_asset_id_from) == Int(0),
                App.globalGet(global_asset_id_to)   == Int(0),
                # Check if the transaction:
                # 1) has the transaction sender equal to the current administrator address;
                # 2) has the payment's receiver address equal to the address of the application;
                # 3) has the rekey address set to a zero address;
                # 4) has the close remainder address set to a zero address;
                # 5) has the asset close address set to a zero address.
                txn.get().sender()             == App.globalGet(global_admin),
                txn.get().receiver()           == Global.current_application_address(),
                txn.get().rekey_to()           == Global.zero_address(),
                txn.get().close_remainder_to() == Global.zero_address(),
                txn.get().asset_close_to()     == Global.zero_address()
            )
        ),
        # Opt-in into starting asset.
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields
        (
            {
                TxnField.type_enum     : TxnType.AssetTransfer,
                TxnField.fee           : Int(0),
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
                TxnField.fee           : Int(0),
                TxnField.xfer_asset    : asset_id_to.get(),
                TxnField.asset_receiver: Global.current_application_address(),
            }
        ),
        InnerTxnBuilder.Submit(),
        # Set source and destination assets.
        App.globalPut(global_asset_id_from, asset_id_from.get()),
        App.globalPut(global_asset_id_to, asset_id_to.get()),
        Approve()
    )


@router.method(no_op=CallConfig.CALL)
def swap(
    txn: abi.AssetTransferTransaction
) -> Expr:
    """
        Swap asset.

        Args:
            txn: asset transfer transaction.
    """
    asset_to_transfer  = ScratchVar(TealType.uint64)
    amount_to_transfer = ScratchVar(TealType.uint64)
    rate_decimals      = ScratchVar(TealType.uint64)

    return Seq(
        Assert(
            And(
                # Check if the first transaction in the group:
                # 1) has the asset to be transfered parameter equal 
                #    to the source/destination asset set as global variable;
                # 2) has the asset amount parameter greater than 0;
                # 3) has the asset receiver address equal to the current application
                #    address;
                # 4) has the rekey address set to a zero address;
                # 5) has the close remainder address set to a zero address;
                # 6) has the asset close address set to a zero address.
                Or(
                    txn.get().xfer_asset() == App.globalGet(global_asset_id_from),
                    txn.get().xfer_asset() == App.globalGet(global_asset_id_to)
                ),
                txn.get().asset_amount()       >  Int(0),
                txn.get().asset_receiver()     == Global.current_application_address(),
                txn.get().rekey_to()           == Global.zero_address(),
                txn.get().close_remainder_to() == Global.zero_address(),
                txn.get().asset_close_to()     == Global.zero_address(),
            )
        ),
        # In order to calculate the swapped token amount, we need to use the eq.:
        #                              y = x * R / 10^r,                                                                           
        # where:
        # - y is the amount of the swapped token;
        # - x is the amount of the token to swap;
        # - R is the integer part of the rate value;
        # - r is the number of decimals in the rate value.
        #
        # Check if:
        # 1)  the rate global variable is set;
        # 2a) in case the asset ID is equal to the source asset global variable,
        #     check if the quantity y = x * R / 10^r doesn't overflow;
        # 2b) in case the asset ID is equal to the destination asset global va-
        #     riable, check if the quantity x = y * 10^r / R doesn't overflow.
        Assert(
            App.globalGet(global_rate_integer) > Int(0)
        ),
        rate_decimals.store(Exp(Int(10), App.globalGet(global_rate_decimal))),
        If(
            txn.get().xfer_asset() == App.globalGet(global_asset_id_from),
        ).
        Then(
            Assert(
                # Assuming that, in the division A * B, B is greater than 0, we have to
                # check if the product of the multiplication doesn't overflow.
                amount_to_transfer.store(
                    txn.get().asset_amount() * App.globalGet(global_rate_integer) / rate_decimals.load()
                )
            ),
            asset_to_transfer.store(
                App.globalGet(global_asset_id_to)
            )
        ).
        Else(
            Assert(
                # Assuming that, in the division A / B, B is greater than 0, we have to
                # check if the quotient of the division doesn't overflow (It may happen
                # in the case of A >> B).
                amount_to_transfer.store(
                    txn.get().asset_amount() * rate_decimals.load() / App.globalGet(global_rate_integer)
                )
            ),
            asset_to_transfer.store(
                App.globalGet(global_asset_id_from)
            )
        ),
        # Swap tokens.
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum     : TxnType.AssetTransfer,
                TxnField.fee           : Int(0),
                TxnField.asset_receiver: txn.get().sender(),
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
    with open("../../build/clear.teal"   , "w") as f:
        f.write(clear_state_program)
    with open("api.json", "w") as f:
        f.write(
            json.dumps(
                contract.dictify(), 
                indent=4
            )
        )
