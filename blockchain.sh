#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
PID_DIR="$PROJECT_DIR/.pids"
BASE_PORT=8000
WEB_OFFSET=1000

usage() {
    echo "Usage: ./blockchain.sh <command> [args]"
    echo ""
    echo "Commands:"
    echo "  setup          Create virtual environment and install dependencies"
    echo "  start <N>      Start N nodes (ports ${BASE_PORT}, $(( BASE_PORT + 1 )), ...)"
    echo "  status         Show running nodes"
    echo "  stop           Stop all running nodes"
    echo "  logs <port>    Tail logs for a specific node"
    echo "  clean          Stop nodes and remove venv, generated files"
    exit 1
}

ensure_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        echo "Error: venv not found. Run './blockchain.sh setup' first."
        exit 1
    fi
}

cmd_setup() {
    echo "==> Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "==> Installing dependencies..."
    "$VENV_DIR/bin/pip" install --upgrade pip -q
    "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt" -q
    echo "==> Setup complete!"
}

cmd_start() {
    local n="${1:-}"
    if [ -z "$n" ] || ! [[ "$n" =~ ^[0-9]+$ ]] || [ "$n" -lt 1 ]; then
        echo "Usage: ./blockchain.sh start <number_of_nodes>"
        exit 1
    fi

    ensure_venv
    mkdir -p "$PID_DIR"
    mkdir -p "$PROJECT_DIR/logs"

    # Check if nodes are already running
    if ls "$PID_DIR"/*.pid 1>/dev/null 2>&1; then
        echo "Nodes are already running. Run './blockchain.sh stop' first."
        exit 1
    fi

    # Generate peer lists
    local ports=()
    for (( i=0; i<n; i++ )); do
        ports+=( $(( BASE_PORT + i )) )
    done

    for (( i=0; i<n; i++ )); do
        local port=${ports[$i]}
        local node_file="$PID_DIR/nodes_${port}.txt"
        > "$node_file"
        for (( j=0; j<n; j++ )); do
            if [ $j -ne $i ]; then
                echo "localhost:${ports[$j]}" >> "$node_file"
            fi
        done
    done

    # Start nodes
    for (( i=0; i<n; i++ )); do
        local port=${ports[$i]}
        local web_port=$(( port + WEB_OFFSET ))
        local node_file="$PID_DIR/nodes_${port}.txt"
        local log_file="$PROJECT_DIR/logs/node_${port}.log"

        "$VENV_DIR/bin/python3" "$PROJECT_DIR/node.py" "$port" "$node_file" \
            > "$log_file" 2>&1 &
        local pid=$!
        echo "$pid" > "$PID_DIR/${port}.pid"
        echo "  Node :${port}  dashboard http://localhost:${web_port}  (PID ${pid})"
    done

    echo ""
    echo "==> ${n} node(s) started!"
}

cmd_status() {
    if [ ! -d "$PID_DIR" ] || ! ls "$PID_DIR"/*.pid 1>/dev/null 2>&1; then
        echo "No nodes running."
        return
    fi

    echo "Running nodes:"
    echo ""
    for pid_file in "$PID_DIR"/*.pid; do
        local port
        port="$(basename "$pid_file" .pid)"
        local pid
        pid="$(cat "$pid_file")"
        local web_port=$(( port + WEB_OFFSET ))

        if kill -0 "$pid" 2>/dev/null; then
            echo "  Node :${port}  dashboard http://localhost:${web_port}  (PID ${pid}) ✓"
        else
            echo "  Node :${port}  (PID ${pid}) ✗ dead"
        fi
    done
}

cmd_stop() {
    if [ ! -d "$PID_DIR" ] || ! ls "$PID_DIR"/*.pid 1>/dev/null 2>&1; then
        echo "No nodes running."
        return
    fi

    echo "==> Stopping nodes..."
    for pid_file in "$PID_DIR"/*.pid; do
        local port
        port="$(basename "$pid_file" .pid)"
        local pid
        pid="$(cat "$pid_file")"

        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            echo "  Stopped node :${port} (PID ${pid})"
        fi
        rm -f "$pid_file"
    done

    # Clean up generated peer lists
    rm -f "$PID_DIR"/nodes_*.txt
    rmdir "$PID_DIR" 2>/dev/null || true
    echo "==> All nodes stopped."
}

cmd_logs() {
    local port="${1:-}"
    if [ -z "$port" ]; then
        echo "Usage: ./blockchain.sh logs <port>"
        exit 1
    fi
    local log_file="$PROJECT_DIR/logs/node_${port}.log"
    if [ ! -f "$log_file" ]; then
        echo "No log file for port ${port}."
        exit 1
    fi
    tail -f "$log_file"
}

cmd_clean() {
    cmd_stop 2>/dev/null || true
    echo "==> Removing venv and generated files..."
    rm -rf "$VENV_DIR"
    rm -rf "$PROJECT_DIR/logs"
    rm -rf "$PID_DIR"
    echo "==> Clean complete."
}

# --- Main ---
command="${1:-}"
shift || true

case "$command" in
    setup)  cmd_setup ;;
    start)  cmd_start "$@" ;;
    status) cmd_status ;;
    stop)   cmd_stop ;;
    logs)   cmd_logs "$@" ;;
    clean)  cmd_clean ;;
    *)      usage ;;
esac
