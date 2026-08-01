# Blockchain Node

A simplified blockchain network where multiple nodes run locally, exchange transactions, and reach consensus on new blocks.

![Dashboard Screenshot](screenshot.png)

## About

Each node maintains its own copy of the blockchain, accepts transactions, proposes blocks, and communicates with peers to reach consensus. The system demonstrates core distributed systems concepts: chain validation, hash-linked blocks, round-based consensus, mempool management, and peer-to-peer broadcasting.

A web dashboard was added separately to visualise each node's chain state, mempool, and connected peers.

## How to Run

```bash
./blockchain.sh setup          # create venv and install dependencies
./blockchain.sh start 3        # start 3 nodes (ports 8000, 8001, 8002)
./blockchain.sh status         # check running nodes
./blockchain.sh logs 8000      # tail logs for a specific node
./blockchain.sh stop           # stop all nodes
```

Each node gets a dashboard at `http://localhost:<port + 1000>`.

## Architecture

| Module | Responsibility |
|--------|---------------|
| `blockchain.py` | Chain state, block validation, serialisation |
| `consensus.py` | Round-based consensus: propose → decide → commit |
| `block.py` | Block data structure |
| `transaction.py` | Transaction data structure |
| `mempool.py` | Pending transaction pool, committed transaction cleanup |
| `network.py` | Peer-to-peer communication, block/transaction broadcasting |
| `node.py` | Node orchestration — ties all modules together |
| `api.py` | Web dashboard and REST endpoints |
| `utils.py` | Hashing utilities |

## Key Concepts Implemented

- **Hash-linked chain** — each block stores the hash of the previous block, forming an immutable sequence
- **Chain validation** — verifies index continuity, hash linkage, and genesis block consistency across the full chain
- **Round-based consensus** — nodes propose blocks from their mempool, validate peer proposals, and commit the decided block
- **Peer discovery** — nodes are configured with peer lists and broadcast transactions and blocks to all connected peers
- **Genesis block** — deterministic creation ensures all nodes start from the same state

## Course Context

Built for COMP3221 (Distributed Systems) at the University of Sydney, 2025. Scored 96/100.

## Transparency

This project was built with significant assistance from Claude Code (AI coding tool). The web dashboard (`api.py`) was not part of the original assignment scope — I added it afterward because I wanted users to be able to see what each node is doing. The core distributed systems concepts (consensus rounds, chain validation, peer communication) are what I studied and understood through the course.

## What I'd do differently today

- **Add fault tolerance:** The current consensus assumes all nodes are online and honest. Implementing a Byzantine fault tolerant protocol (like PBFT) would make the system more realistic.
- **Separate the dashboard:** `api.py` bundles REST endpoints and HTML rendering. Splitting the API layer from the frontend would make each easier to extend independently.
