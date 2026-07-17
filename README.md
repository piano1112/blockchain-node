# Blockchain Node

A peer-to-peer blockchain network simulation in Python. Nodes communicate over TCP, validate transactions using Ed25519 cryptographic signatures, and reach consensus to maintain a shared ledger.

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
```

## Getting Started

### Prerequisites

- Python 3.8+
- [PyNaCl](https://pynacl.readthedocs.io/) (libsodium bindings for Ed25519)

### Installation

```bash
git clone https://github.com/piano1112/blockchain-node.git
cd blockchain-node
pip install -r requirements.txt
```

### Running a Node

Create a `nodes.txt` file listing peer addresses:

```
localhost:8001
localhost:8002
```

Start a node:

```bash
./Run.sh 8000 nodes.txt
```

To run a multi-node network locally, start each node in a separate terminal with a different port. Enable debug logging with:

```bash
NODE_DEBUG=1 ./Run.sh 8000 nodes.txt
```

## Key Design Decisions

- **Lowest-hash consensus**: When multiple valid block proposals exist, nodes deterministically select the block with the lowest SHA-256 hash, ensuring all nodes converge on the same chain without a leader.
- **Nonce-based ordering**: Each sender's transactions must arrive with sequential nonces (0, 1, 2, ...), preventing replay attacks and ensuring transaction ordering.
- **Thread-per-peer networking**: Each peer connection runs in its own thread with length-prefixed message framing for reliable delivery.
- **Graceful idle shutdown**: The consensus loop exits after 5 seconds of inactivity, allowing the process to terminate naturally after a test run.

## Technical Highlights

- **Cryptographic verification**: Transactions are signed with Ed25519 (via PyNaCl/libsodium) and verified before entering the mempool
- **Thread-safe mempool**: Concurrent access from network handlers and the consensus loop is managed with locks
- **Canonical hashing**: Block hashes are computed over deterministically serialised JSON for cross-node consistency
- **Fault tolerance**: Crashed peers are detected via timeouts and excluded from subsequent consensus rounds
