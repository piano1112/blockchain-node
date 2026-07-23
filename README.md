# Blockchain Node

A peer-to-peer blockchain network simulation in Python. Nodes communicate over TCP, validate transactions using Ed25519 cryptographic signatures, and reach consensus to maintain a shared ledger. Includes a real-time web dashboard for monitoring and interaction.

Built as part of COMP3221 (Distributed Systems) at the University of Sydney.

## How It Works

Each node runs as a standalone process. When a signed transaction arrives, the node validates it, adds it to its local mempool, and broadcasts it to peers. Periodically, nodes enter a **consensus round**: each proposes a block from its mempool, exchanges proposals with peers over TCP, and all nodes agree on the same block (the one with the lowest hash) to append to the chain.

Transactions use **Ed25519 signatures** for authentication — each sender signs their message with a private key, and nodes verify the signature against the sender's public key before accepting the transaction.

## Architecture

```
node.py           → Main entry point, consensus loop orchestration
network.py        → TCP server/client, peer connections, message framing
consensus.py      → Block proposal, validation, and commit logic
blockchain.py     → Chain state, genesis block, chain validation
block.py          → Block data structure, serialisation
mempool.py        → Transaction pool with nonce tracking and eviction
transaction.py    → Transaction model, Ed25519 signature verification
utils.py          → Canonical JSON hashing (SHA-256)
api.py            → FastAPI web dashboard and REST API
blockchain.sh     → Lifecycle management script
```

## Getting Started

### Prerequisites

- Python 3.8+

### Quick Start

```bash
git clone https://github.com/piano1112/blockchain-node.git
cd blockchain-node
./blockchain.sh setup
./blockchain.sh start 3
```

This sets up the virtual environment, installs dependencies, and launches a 3-node network. Each node gets a web dashboard:

- Node 8000 → http://localhost:9000
- Node 8001 → http://localhost:9001
- Node 8002 → http://localhost:9002

### Lifecycle Management

```bash
./blockchain.sh setup          # Create venv and install dependencies
./blockchain.sh start <N>      # Start N nodes
./blockchain.sh status         # Show running nodes
./blockchain.sh logs <port>    # Tail logs for a specific node
./blockchain.sh stop           # Stop all nodes
./blockchain.sh clean          # Stop nodes, remove venv and logs
```

## Web Dashboard

Each node serves a real-time dashboard on its port + 1000. The dashboard displays:

- **Blockchain state** — block list with hashes, indices, and transaction counts
- **Mempool** — pending transactions awaiting consensus
- **Peer status** — connection state of each peer (connected / connecting / crashed)
- **Transaction submission** — send signed transactions directly from the browser

### REST API

The dashboard also exposes a JSON API:

| Endpoint | Method | Description |
|---|---|---|
| `/api/node` | GET | Node info (port, chain length, public key) |
| `/api/blockchain` | GET | Full chain with all blocks |
| `/api/mempool` | GET | Pending transactions |
| `/api/peers` | GET | Peer connection status |
| `/api/transaction` | POST | Submit a signed transaction |

## Key Design Decisions

- **Lowest-hash consensus**: When multiple valid block proposals exist, nodes deterministically select the block with the lowest SHA-256 hash, ensuring all nodes converge on the same chain without a leader.
- **Nonce-based ordering**: Each sender's transactions must arrive with sequential nonces (0, 1, 2, ...), preventing replay attacks and ensuring transaction ordering.
- **Thread-per-peer networking**: Each peer connection runs in its own thread with length-prefixed message framing for reliable delivery.
- **Automatic peer reconnection**: Crashed peers are periodically retried, allowing nodes to rejoin the network after downtime.

## Technical Highlights

- **Cryptographic verification**: Transactions are signed with Ed25519 (via PyNaCl/libsodium) and verified before entering the mempool
- **Thread-safe mempool**: Concurrent access from network handlers and the consensus loop is managed with locks
- **Canonical hashing**: Block hashes are computed over deterministically serialised JSON for cross-node consistency
- **Fault tolerance**: Crashed peers are detected via timeouts, excluded from consensus rounds, and automatically reconnected
- **Real-time monitoring**: FastAPI-powered dashboard with auto-refreshing UI and REST API for programmatic access