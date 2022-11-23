# How To Run This Contract?

1. Compile the TEAL code.

```
    ./build.sh contracts.rps.contract
```

2. Enter inside the Algorand Sandbox container.

```
    cd ../sandbox
    ./sandbox enter algod
```

3. Deploy the contract.

```
    goal app create --creator <address-creator> --approval-prog /data/build/approval.teal --clear-prog /data/build/clear.teal --global-byteslices 0 --global-ints 0  --local-byteslices 3 --local-ints 1
```

4. Modify the variables `APP_ID`, `APP_ACCOUNT`, `CHALLENGER_ACCOUNT`, and `OPPONENT_ACCOUNT` in the file `config.sh` accordingly to the application information and the challenger and opponent accounts.

5. Opt-In challenger and opponent accounts.

```
    goal app optin --app-id <app_id> --from <challenger_address>
    goal app optin --app-id <app_id> --from <opponent_address>
```

6. Create and execute a group of two transactions: 
    * the first one is responsible for creating the challenge; 
    * the second one is responsible for sending the wager.

```
    /data/contracts/rps/challenge.sh
```

7. Create and execute a group of two transactions: 
    * the first one is responsible for accepting the challenge; 
    * the second one is responsible for sending the wager proposed by the challenger.

```
    /data/contracts/rps/accept.sh
``` 

8. Compute the play results and send rewards/wagers to players.

```
    /data/contracts/rps/reveal.sh
```

**N.B.** The last operation can fail in case the application account balance is below the minimum requested balance. In this case, fund the application account balance.

```
    goal clerk app send -f <from_address> -t <application_address> -a 100000
```
