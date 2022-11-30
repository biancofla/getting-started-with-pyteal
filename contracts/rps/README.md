# How To Run This Contract?

1. Compile the TEAL code.

```
    ./build.sh contracts.rps.contract
```

2. Enter inside the contract folder.

```
    cd ./contracts/rps/
```

3. Modify the value of the variable `GENESIS_ADDRESS` inside the file `run.py`.

4. Modify the values of the variables `CHALLENGER_REVEAL` and `OPPONENT_REVEAL` according to game with you want to simulate.

4. Deploy/Execute the contract.

```
    python ./run.py
```