This WIP library runs the [dao-treasury](https://github.com/BobTheBuidler/dao-treasury) exporter for the [Yearn Finance](https://yearn.fi/) treasury.

## Installation

- **pip:**
  ```bash
   pip install yearn-treasury
  ```

- **From Source:**  
  ```bash
  git clone https://github.com/BobTheBuidler/yearn-treasury
  cd yearn-treasury
  poetry install
  ```

## Requirements
- Python 3.10 or higher.
- At least 16GB of RAM.
- All dependencies installed as specified in the project’s pyproject.toml file.

## Prerequisites

- First, you will need to bring your own archive node. This can be one you run yourself, or one from one of the common providers (Tenderly, Alchemy, QuickNode, etc.). Your archive node must have tracing enabled (free-tier Alchemy nodes do not support this option).
- You must configure a [brownie network](https://eth-brownie.readthedocs.io/en/stable/network-management.html) to use your RPC.
- You will need an auth token for [Etherscan](https://etherscan.io/)'s API. Follow their [guide](https://docs.etherscan.io/etherscan-v2/getting-an-api-key) to get your key, and set env var `ETHERSCAN_TOKEN` with its value.
- You'll also need [Docker](https://www.docker.com/get-started/) installed on your system. If on MacOS, you will need to leave Docker Desktop open while Yearn Treasury is running.

## Usage

Run the treasury export tool:

```bash
# For pip installations:
yearn-treasury --network mainnet --interval 12h
```

For local development (from source installation), use:
```bash
poetry run yearn-treasury --network mainnet --interval 12h
```

**CLI Options:**
- `--network`: The id of the brownie network the exporter will connect to (default: mainnet)
- `--interval`: The time interval between each data snapshot (default: 12h)
- `--daemon`: Run the export process in the background (default: False) (NOTE: currently unsupported)
- `--grafana-port`: Set the port for the Grafana dashboard where you can view data (default: 3004)
- `--renderer-port`: Set the port for the report rendering service (default: 8080)
- `--victoria-port`: Set the port for the Victoria metrics reporting endpoint (default: 8430)

After running the command, the export script will run continuously until you close your terminal.
To access the dashboard, open your browser and navigate to [http://localhost:3004](http://localhost:3004) for the [dao-treasury](https://github.com/BobTheBuidler/dao-treasury) dashboard.

Enjoy!

## Screenshots

#### [Transactions Dashboard](https://bobthebuidler.github.io/yearn-treasury/transactions.html)

![image](https://github.com/user-attachments/assets/4293b62d-827a-4bae-af4f-014c99511f99)
