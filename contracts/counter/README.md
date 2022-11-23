# How To Run This Contract?

1. Compile the TEAL code.

```
    ./build.sh contracts.counter.contract
```

2. Enter inside the Algorand Sandbox container.

```
    cd ../sandbox
    ./sandbox enter algod
```

3. Deploy the contract.

```
    goal app create --creator <address-creator> --approval-prog /data/build/approval.teal --clear-prog /data/build/clear.teal --global-byteslices 1 --global-ints 1  --local-byteslices 0 --local-ints 0
```

4. In order to increase the contracts's global counter, execute a No-Op call to the contract with the string argument `inc`. Viceversa, to decrease the counter, execute a No-Op call to the contract with the string argument `dec`.

```
    goal app call --app-id <app-id> --from <from-address> --app-arg ["str:inc"|"str:dec"]
```