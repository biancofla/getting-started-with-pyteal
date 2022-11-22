from pyteal import *

from pyteal_helpers import program

def approval():
    # Local variables.
    local_opponent   = Bytes("opponent")
    local_wager      = Bytes("wager")
    local_commitment = Bytes("commitment")
    local_reveal     = Bytes("reveal")
    # Operations.
    op_challenge     = Bytes("challenge")
    op_accept        = Bytes("accept")
    op_reveal        = Bytes("reveal")

    return program.event(
        init=Approve(),
        opt_in=Seq(
            reset(
                Int(0)          ,
                local_opponent  ,
                local_wager     ,
                local_commitment,
                local_reveal
            ),
            Approve()
        ),
        no_op=Seq(
            Cond(
                [
                    Txn.application_args[0] == op_challenge, 
                    create_challenge(
                        local_opponent  ,
                        local_wager     ,
                        local_commitment,
                        local_reveal    
                    )
                ],
                [
                    Txn.application_args[0] == op_accept,
                    accept_challenge(
                        local_opponent,
                        local_wager   ,
                        local_reveal   
                    )
                ],
                [
                    Txn.application_args[0] == op_reveal, 
                    reveal(
                        local_opponent  ,
                        local_wager     ,
                        local_commitment,
                        local_reveal    
                    )
                ]
            ),
            Reject()
        )
    )

@Subroutine(TealType.none)
def reset(
    account         , 
    local_opponent  , 
    local_wager     , 
    local_commitment, 
    local_reveal
):
    """
        Reset account local state.
    """
    return Seq(
        App.localPut(account, local_opponent  , Bytes("")),
        App.localPut(account, local_wager     , Int(0)   ),
        App.localPut(account, local_commitment, Bytes("")),
        App.localPut(account, local_reveal    , Bytes(""))
    )

@Subroutine(TealType.none)
def create_challenge(
    local_opponent  , 
    local_wager     , 
    local_commitment, 
    local_reveal
):
    """
        Create challenge.
    """
    return Seq(
        program.check_self(group_size=Int(2), group_index=Int(0)),
        program.check_rekey_zero(2),
        Assert(
            And(
                # Check if:
                # 1) the second transaction in the group is a payment transaction;
                # 2) the payment's receiver has the same address of the application;
                # 3) the close remainder address is a zero address.
                Gtxn[1].type_enum()          == TxnType.Payment,
                Gtxn[1].receiver()           == Global.current_application_address(),
                Gtxn[1].close_remainder_to() == Global.zero_address(),
                # Check if the opponent account has opted in.
                App.optedIn(Txn.accounts[1], Global.current_application_id()),
                # Check accounts availability to play.
                _are_available_to_play(
                    Txn.sender()    ,
                    Txn.accounts[1] ,
                    local_opponent  ,
                    local_wager     ,
                    local_commitment,
                    local_reveal
                ),
                # Check if the number of arguments passed is valid.
                Txn.application_args.length() == Int(2)
            )
        ),
        # Update challenger local state.
        App.localPut(Txn.sender(), local_opponent  , Txn.accounts[1]        ),
        App.localPut(Txn.sender(), local_wager     , Gtxn[1].amount()       ),
        App.localPut(Txn.sender(), local_commitment, Txn.application_args[1]),
        Approve()
    )

@Subroutine(TealType.uint64)
def _are_available_to_play(
    challenger      , 
    opponent        , 
    local_opponent  , 
    local_wager     , 
    local_commitment, 
    local_reveal
):
    """
        Check if both accounts - the challenger and the opponent - 
        are not involved in any other "Rock, Paper, Scissors" game.
    """
    return Return(
        And(
            # Check challenger account availability.
            App.localGet(challenger, local_opponent  ) == Bytes(""),
            App.localGet(challenger, local_wager     ) == Int(0)   ,
            App.localGet(challenger, local_commitment) == Bytes(""),
            App.localGet(challenger, local_reveal    ) == Bytes(""),
            # Check opponent account availability.
            App.localGet(opponent, local_opponent  ) == Bytes(""),
            App.localGet(opponent, local_wager     ) == Int(0)   ,
            App.localGet(opponent, local_commitment) == Bytes(""),
            App.localGet(opponent, local_reveal    ) == Bytes(""),
        )
    )

@Subroutine(TealType.none)
def accept_challenge(
    local_opponent, 
    local_wager   , 
    local_reveal
):
    """
        Accept challenge.
    """
    return Seq(
        program.check_self(group_size=Int(2), group_index=Int(0)),
        program.check_rekey_zero(2),
        Assert(
            And(
                # Check if the challenger account has opted in.
                App.optedIn(Txn.accounts[1], Global.current_application_id()),
                # Check if the challenger's opponent is this specific account.
                App.localGet(Txn.accounts[1], local_opponent) == Txn.sender(),
                # Check if:
                # 1) the second transaction in the group is a payment transaction;
                # 2) the payment's receiver has the same address of the application;
                # 3) the close remainder address is a zero address;
                # 4) the wager amount is the same proposed by the challenger.
                Gtxn[1].type_enum()          == TxnType.Payment,
                Gtxn[1].receiver()           == Global.current_application_address(),
                Gtxn[1].close_remainder_to() == Global.zero_address(),
                Gtxn[1].amount()             == App.localGet(Txn.accounts[1], local_wager),
                # Check if the number of arguments passed is valid.
                Txn.application_args.length() == Int(2),
                # Check if the play is valid.
                _is_a_valid_play(Txn.application_args[1])
            )
        ),
        # Update opponent local state.
        App.localPut(Txn.sender(), local_opponent, Txn.accounts[1]        ),
        App.localPut(Txn.sender(), local_wager   , Gtxn[1].amount()       ),
        App.localPut(Txn.sender(), local_reveal  , Txn.application_args[1]),
        Approve()
    )

@Subroutine(TealType.uint64)
def _is_a_valid_play(play):
    """
        Check if the play is valid. 
    """
    first_character = ScratchVar(TealType.bytes)
    return Seq(
        first_character.store(Substring(play, Int(0), Int(1))),
        Return(
            Or(
                first_character.load() == Bytes("r"),
                first_character.load() == Bytes("p"),
                first_character.load() == Bytes("s"),
            )
        )
    )

@Subroutine(TealType.none)
def reveal(
    local_opponent  , 
    local_wager     , 
    local_commitment, 
    local_reveal
):
    """
        Do the reveal operation.
    """
    challenger_play = ScratchVar(TealType.uint64)
    opponent_play   = ScratchVar(TealType.uint64)
    wager           = ScratchVar(TealType.uint64)
    return Seq(
        program.check_self(group_size=Int(1), group_index=Int(0)),
        program.check_rekey_zero(1),
        Assert(
            And(
                # Check mutual opponentship.
                App.localGet(Txn.sender()   , local_opponent) == Txn.accounts[1],
                App.localGet(Txn.accounts[1], local_opponent) == Txn.sender(),
                # Check if challenger and opponent has the same wager.
                App.localGet(Txn.sender(), local_wager) == App.localGet(Txn.accounts[1], local_wager),
                # Check commitment from the challenger account is not empty.
                App.localGet(Txn.sender(), local_commitment) != Bytes(""),
                # Check reveal from the opponent account is not empty. 
                App.localGet(Txn.accounts[1], local_reveal) != Bytes(""),
                # Check commit/reveal from challenger.
                Txn.application_args.length() == Int(2),
                Sha256(Txn.application_args[1]) == App.localGet(Txn.sender(), local_commitment)
            )
        ),
        # Use scratch variables to store players' plays and the wager.
        challenger_play.store(_play_to_value(Txn.application_args[1])),
        opponent_play.store(_play_to_value(App.localGet(Txn.accounts[1], local_reveal))),
        wager.store(App.localGet(Txn.sender(), local_wager)),
        # Distribute rewards or, in case of a tie game, return wagers.
        If (
            challenger_play.load() == opponent_play.load()
        )
        .Then(
            # Tie case - Return wagers.
            Seq(
                # Make sure the fee covers the cost of the no-op operation
                # plus the two inner transactions to return wagers.
                Assert(
                    Txn.fee() >= Global.min_txn_fee() * Int(3)
                ),
                send_amount(Int(0), wager.load()),
                send_amount(Int(1), wager.load()),
            )
        )
        .Else(
            # Win case - Send rewards.
            Seq(
                # Make sure the fee covers the cost of the no-op operation
                # plus the inner transaction to reward the winner.
                Assert(
                    Txn.fee() >= Global.min_txn_fee() * Int(2)
                ),
                send_amount(
                    compute_winner(challenger_play.load(), opponent_play.load()),
                    wager.load() * Int(2)
                )
            )
        ),
        # Reset local states.
        reset(
            Txn.sender()    ,
            local_opponent  ,
            local_wager     ,
            local_commitment,
            local_reveal
        ),
        reset(
            Txn.accounts[1] ,
            local_opponent  ,
            local_wager     ,
            local_commitment,
            local_reveal
        ),
        Approve()
    )

@Subroutine(TealType.uint64)
def _play_to_value(play):
    """
        Map account's play to a discrete value.
    """
    first_character = ScratchVar(TealType.bytes)
    return Seq(
        first_character.store(Substring(play, Int(0), Int(1))),
        Return(
            Cond(
                [first_character.load() == Bytes("r"), Int(0)],
                [first_character.load() == Bytes("p"), Int(1)],
                [first_character.load() == Bytes("s"), Int(2)]
            )
        )
    )

@Subroutine(TealType.uint64)
def compute_winner(challenger_play, opponent_play):
    """
        Return the index of the winner account.
    """
    return Return(
        Cond(
            [((opponent_play   + Int(1)) % Int(3)) == challenger_play, Int(0)],
            [((challenger_play + Int(1)) % Int(3)) == opponent_play  , Int(0)],
        )
    )

@Subroutine(TealType.none)
def send_amount(account_index, amount):
    """
        Send an amount to the account specified by the account index.
    """
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.receiver : Txn.accounts[account_index],
                TxnField.amount   : amount,
                TxnField.fee      : Int(0)
            }
        ),
        InnerTxnBuilder.Submit()
    )

def clear():
    return Approve()