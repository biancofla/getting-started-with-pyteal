# Getting Started With PyTeal

This repository contains all the projects I implemented during the process of study of PyTeal.

### Prerequisities

The only prerequisite for this project is [Docker](https://docs.docker.com/get-docker/).

## Setup

1. Create a parent directory and change the current directory to this very one.

```
   mkdir $HOME/algorand-workspace && cd $HOME/algorand-workspace
```

2. Clone the [Algorand Sandbox](https://github.com/algorand/sandbox) project repository. 

```
  git clone https://github.com/algorand/sandbox
```

3. Clone the project repository.

```
  git clone https://github.com/biancofla/getting-started-with-pyteal
```

4. Add the project folder as bind volume in `docker-compose.yml`, as the last element of the key `services.algod`. The `docker-compose.yml` file is inside the `sandbox` folder.

```yml
  volumes:
  - type: bind
    source: ../getting-started-with-pyteal
    target: /data
```

5. Run the Algorand Sandbox.

```
  cd ./sandbox
  ./sandbox up
```

6. Inside the project folder, install a Python virtual environment and activate it.

```
  cd ../getting-started-with-pyteal
  python -m venv venv
  source ./venv/bin/activate
```

7. Install the required Python modules.

```
  python -m pip install -r ./requirements.txt
```

To run one of the contracts, have a look at these `README.md` files:

* [Counter](https://github.com/biancofla/getting-started-with-pyteal/tree/main/contracts/counter)
* [Rock, Paper, Scissors](https://github.com/biancofla/getting-started-with-pyteal/tree/main/contracts/rps)
