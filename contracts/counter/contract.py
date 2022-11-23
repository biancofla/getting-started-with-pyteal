from pyteal import * 

from pyteal_helpers import program

UINT64_MAX = 0xffffffffffffffff

def approval():
    # Global variables.
    global_owner   = Bytes("owner")
    global_counter = Bytes("counter")
    # Operations.
    op_increment   = Bytes("inc")
    op_decrement   = Bytes("dec")

    return program.event(
        init=Seq(
            App.globalPut(global_owner  , Txn.sender()),
            App.globalPut(global_counter, Int(0)      ),
            Approve()
        ),
        no_op=Seq(
            Cond(
                [
                    Txn.application_args[0] == op_increment, 
                    Seq(
                        modify_counter(
                            Int(0),
                            global_counter
                        ),
                        Approve()
                    )
                ],
                [
                    Txn.application_args[0] == op_decrement, 
                    Seq(
                        modify_counter(
                            Int(1),
                            global_counter
                        ),
                        Approve()
                    )
                ]
            ),
            Reject()
        ) 
    )

@Subroutine(TealType.none)
def modify_counter(case, global_counter):
    """
        Increment/Decrement counter global value.
    """
    scratch_counter = ScratchVar(TealType.uint64)
    return Seq(
        scratch_counter.store(App.globalGet(global_counter)),
        Cond(
            [
                case == Int(0),
                # To avoid an overflow exception due to the uint64 type used 
                # to define the counter variable, we check if the counter 
                # current value is lesser than 2^64 - 1. If so, the increment 
                # operation can be performed.
                If(
                    scratch_counter.load() < Int(UINT64_MAX)
                )
                .Then(
                    App.globalPut(global_counter, scratch_counter.load() + Int(1)),
                )
            ],
            [
                case == Int(1),
                # Analogous to the case of the increment operation, we check if 
                # the counter current value is greater than 0. If so, the decrement 
                # operation can be performed.
                If(
                    scratch_counter.load() > Int(0)
                )
                .Then(
                    App.globalPut(global_counter, scratch_counter.load() - Int(1)),
                )
            ]
        )
    )
    
def clear():
    return Approve()