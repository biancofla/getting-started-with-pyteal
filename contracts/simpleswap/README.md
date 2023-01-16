# How To Build This Contract?

1. Enter inside the contract folder.

```
    cd ./contracts/simpleswap/
```

2. Compile the TEAL code.

```
    python ./src/contract.py
```

# How To Test This Contract?

1. Modify the value of the parameter `passphrase` inside the `Faucet` constructor inside the file `tests/test_base.py` according to the faucet account info.

2. Run the following command.

```
    python -m unittest discover .
```