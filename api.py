import json
import threading
from typing import Any, Dict, List, Optional

import nacl.signing
import nacl.encoding
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Blockchain Node Dashboard")

# Reference to the running Node instance, set by node.py at startup
_node = None


def set_node(node: Any) -> None:
    global _node
    _node = node


# --- API Models ---

class TransactionRequest(BaseModel):
    message: str
    sender: str
    nonce: int
    signature: str


# --- API Endpoints ---

@app.get("/api/blockchain")
def get_blockchain() -> Dict:
    if _node is None:
        raise HTTPException(503, "Node not ready")
    chain = _node.blockchain.chain
    blocks = []
    for block in chain:
        blocks.append({
            "index": block.index,
            "current_hash": block.current_hash,
            "previous_hash": block.previous_hash,
            "transactions": [
                tx.to_dict() if hasattr(tx, "to_dict") else tx
                for tx in block.transactions
            ],
        })
    return {
        "length": len(chain),
        "blocks": blocks,
    }


@app.get("/api/mempool")
def get_mempool() -> Dict:
    if _node is None:
        raise HTTPException(503, "Node not ready")
    txs = _node.mempool.all_transactions()
    return {
        "size": len(txs),
        "transactions": [tx.to_dict() for tx in txs],
    }


@app.get("/api/peers")
def get_peers() -> Dict:
    if _node is None:
        raise HTTPException(503, "Node not ready")
    net = _node.network
    with net._lock:
        connected = set(net._sockets.keys())
        crashed = set(net._crashed)
    peers = []
    for peer in net.peers:
        if peer in crashed:
            status = "crashed"
        elif peer in connected:
            status = "connected"
        else:
            status = "connecting"
        peers.append({"address": peer, "status": status})
    return {
        "total": len(net.peers),
        "active": len(connected - crashed),
        "peers": peers,
    }


@app.post("/api/transaction")
def submit_transaction(tx: TransactionRequest) -> Dict:
    if _node is None:
        raise HTTPException(503, "Node not ready")
    payload = tx.model_dump()
    accepted = _node.submit_transaction(payload)
    if accepted:
        return {"status": "accepted"}
    else:
        raise HTTPException(400, "Transaction rejected")


@app.get("/api/node")
def get_node_info() -> Dict:
    if _node is None:
        raise HTTPException(503, "Node not ready")
    return {
        "port": _node.port,
        "chain_length": len(_node.blockchain.chain),
        "mempool_size": len(_node.mempool),
        "consensus_round": _node.consensus.round,
        "public_key": _node.signing_key.verify_key.encode(
            nacl.encoding.HexEncoder
        ).decode(),
    }


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Blockchain Node Dashboard</title>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --border: #2a2d3a;
    --text: #e1e4ed;
    --text-dim: #8b8fa3;
    --accent: #6c7ee1;
    --green: #4ade80;
    --red: #f87171;
    --yellow: #fbbf24;
    --mono: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 24px;
    max-width: 1200px;
    margin: 0 auto;
  }
  h1 {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 8px;
  }
  .subtitle {
    color: var(--text-dim);
    font-size: 0.85rem;
    margin-bottom: 24px;
  }
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 16px;
  }
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }
  .card-title {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-dim);
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .card-title .dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--accent);
  }
  .stat {
    font-size: 2rem;
    font-weight: 700;
    font-family: var(--mono);
  }
  .full { grid-column: 1 / -1; }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }
  th {
    text-align: left;
    color: var(--text-dim);
    font-weight: 500;
    padding: 8px 12px;
    border-bottom: 1px solid var(--border);
  }
  td {
    padding: 10px 12px;
    border-bottom: 1px solid var(--border);
    font-family: var(--mono);
    font-size: 0.8rem;
    word-break: break-all;
  }
  tr:last-child td { border-bottom: none; }
  .status-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: -apple-system, sans-serif;
  }
  .status-connected { background: #064e3b; color: var(--green); }
  .status-crashed { background: #451a1a; color: var(--red); }
  .status-connecting { background: #422006; color: var(--yellow); }
  .hash { color: var(--accent); }
  .tx-form {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  .tx-form .full-width { grid-column: 1 / -1; }
  input, textarea {
    background: var(--bg);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 10px 12px;
    border-radius: 8px;
    font-family: var(--mono);
    font-size: 0.85rem;
    width: 100%;
    outline: none;
  }
  input:focus, textarea:focus {
    border-color: var(--accent);
  }
  label {
    display: block;
    font-size: 0.75rem;
    color: var(--text-dim);
    margin-bottom: 4px;
  }
  button {
    background: var(--accent);
    color: white;
    border: none;
    padding: 10px 24px;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    font-size: 0.85rem;
  }
  button:hover { opacity: 0.9; }
  .tx-result {
    margin-top: 12px;
    padding: 10px;
    border-radius: 8px;
    font-size: 0.8rem;
    font-family: var(--mono);
    display: none;
  }
  .tx-result.success { display: block; background: #064e3b; color: var(--green); }
  .tx-result.error { display: block; background: #451a1a; color: var(--red); }
  .empty { color: var(--text-dim); font-style: italic; padding: 16px 0; font-size: 0.85rem; }
  .refresh-info {
    text-align: center;
    color: var(--text-dim);
    font-size: 0.75rem;
    margin-top: 16px;
  }
</style>
</head>
<body>

<h1>Blockchain Node</h1>
<div class="subtitle" id="nodeInfo">Loading...</div>

<div class="grid">
  <div class="card">
    <div class="card-title"><span class="dot"></span>Chain Length</div>
    <div class="stat" id="chainLength">-</div>
  </div>
  <div class="card">
    <div class="card-title"><span class="dot"></span>Mempool</div>
    <div class="stat" id="mempoolSize">-</div>
  </div>
</div>

<div class="grid">
  <div class="card full">
    <div class="card-title"><span class="dot" style="background:var(--green)"></span>Peers</div>
    <div id="peersContent"><div class="empty">Loading...</div></div>
  </div>
</div>

<div class="grid">
  <div class="card full">
    <div class="card-title"><span class="dot" style="background:var(--accent)"></span>Blockchain</div>
    <div id="chainContent"><div class="empty">Loading...</div></div>
  </div>
</div>

<div class="grid">
  <div class="card full">
    <div class="card-title"><span class="dot" style="background:var(--yellow)"></span>Mempool Transactions</div>
    <div id="mempoolContent"><div class="empty">Loading...</div></div>
  </div>
</div>

<div class="grid">
  <div class="card full">
    <div class="card-title"><span class="dot" style="background:var(--green)"></span>Submit Transaction</div>
    <div class="tx-form">
      <div>
        <label>Sender (hex public key)</label>
        <input type="text" id="txSender" placeholder="64-char hex">
      </div>
      <div>
        <label>Nonce</label>
        <input type="number" id="txNonce" value="0" min="0">
      </div>
      <div class="full-width">
        <label>Message</label>
        <input type="text" id="txMessage" placeholder="Up to 70 characters" maxlength="70">
      </div>
      <div class="full-width">
        <label>Signature (hex)</label>
        <input type="text" id="txSignature" placeholder="128-char hex signature">
      </div>
      <div class="full-width">
        <button onclick="submitTx()">Submit Transaction</button>
        <div class="tx-result" id="txResult"></div>
      </div>
    </div>
  </div>
</div>

<div class="refresh-info">Auto-refreshes every 2 seconds</div>

<script>
const API = window.location.origin;

async function fetchJSON(path) {
  try {
    const res = await fetch(API + path);
    return await res.json();
  } catch (e) {
    return null;
  }
}

function truncHash(h) {
  if (!h || h.length < 16) return h;
  return h.slice(0, 8) + '...' + h.slice(-8);
}

async function refresh() {
  // Node info
  const info = await fetchJSON('/api/node');
  if (info) {
    document.getElementById('nodeInfo').textContent =
      `Port ${info.port} · Round ${info.consensus_round} · Key ${truncHash(info.public_key)}`;
    document.getElementById('chainLength').textContent = info.chain_length;
    document.getElementById('mempoolSize').textContent = info.mempool_size;
  }

  // Peers
  const peers = await fetchJSON('/api/peers');
  if (peers && peers.peers.length > 0) {
    let html = '<table><tr><th>Address</th><th>Status</th></tr>';
    peers.peers.forEach(p => {
      const cls = 'status-' + p.status;
      html += `<tr><td>${p.address}</td><td><span class="status-badge ${cls}">${p.status}</span></td></tr>`;
    });
    html += '</table>';
    document.getElementById('peersContent').innerHTML = html;
  } else {
    document.getElementById('peersContent').innerHTML = '<div class="empty">No peers configured</div>';
  }

  // Blockchain
  const chain = await fetchJSON('/api/blockchain');
  if (chain && chain.blocks.length > 0) {
    let html = '<table><tr><th>Index</th><th>Hash</th><th>Prev Hash</th><th>Txs</th></tr>';
    // Show newest first
    [...chain.blocks].reverse().forEach(b => {
      html += `<tr>
        <td>${b.index}</td>
        <td class="hash">${truncHash(b.current_hash)}</td>
        <td>${truncHash(b.previous_hash)}</td>
        <td>${b.transactions.length}</td>
      </tr>`;
    });
    html += '</table>';
    document.getElementById('chainContent').innerHTML = html;
  }

  // Mempool
  const mempool = await fetchJSON('/api/mempool');
  if (mempool && mempool.transactions.length > 0) {
    let html = '<table><tr><th>Sender</th><th>Nonce</th><th>Message</th></tr>';
    mempool.transactions.forEach(tx => {
      html += `<tr>
        <td class="hash">${truncHash(tx.sender)}</td>
        <td>${tx.nonce}</td>
        <td>${tx.message}</td>
      </tr>`;
    });
    html += '</table>';
    document.getElementById('mempoolContent').innerHTML = html;
  } else {
    document.getElementById('mempoolContent').innerHTML = '<div class="empty">Mempool is empty</div>';
  }
}

async function submitTx() {
  const result = document.getElementById('txResult');
  const payload = {
    sender: document.getElementById('txSender').value.trim(),
    nonce: parseInt(document.getElementById('txNonce').value),
    message: document.getElementById('txMessage').value,
    signature: document.getElementById('txSignature').value.trim(),
  };
  try {
    const res = await fetch(API + '/api/transaction', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (res.ok) {
      result.className = 'tx-result success';
      result.textContent = 'Transaction accepted';
      document.getElementById('txNonce').value = payload.nonce + 1;
    } else {
      result.className = 'tx-result error';
      result.textContent = data.detail || 'Transaction rejected';
    }
  } catch (e) {
    result.className = 'tx-result error';
    result.textContent = 'Network error: ' + e.message;
  }
}

refresh();
setInterval(refresh, 2000);
</script>
</body>
</html>
"""
