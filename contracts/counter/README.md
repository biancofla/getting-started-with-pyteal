# How To Run This Contract?

1. Compile the TEAL code.

```
    ./build.sh contracts.counter.contract
```

2. Enter inside contract folder and deploy/execute the contract.

```
    cd ./contracts/counter/
```

3. Modify the value of the variable `GENESIS_ADDRESS` inside the file `run.py`.

4. Deploy/Execute the contract.

```
    python ./run.py
```