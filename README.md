# ProgMP MPTCP Scheduler Experiment

This repository contains the implementation of a custom MPTCP scheduler (`mysche.progmp`) using the ProgMP DSL, along with experimental scripts for Mininet.

## Project Structure

- `mysche.progmp`: The custom MPTCP scheduler implementation.
- `run_exp.py`: Main experiment runner script for Mininet.
- `test_sender.py`: Python script for sending data and configuring the scheduler via ProgMP API.
- `test_receiver.py`: Python script for receiving data and calculating throughput.
- `mptcp-topo1.py`: Mininet topology script (4 subflows).
- `api/`: ProgMP Python API and examples.
- `progmp可用算法/`: Reference algorithms (MinRTT, RoundRobin, Redundant).
- `代码编写需求.md`: Original requirements documentation.
- `progmp使用方法.md`: ProgMP DSL documentation.

## How to Run

1.  **Environment**: Requires a Linux kernel with ProgMP support and Mininet installed.
2.  **Setup**:
    ```bash
    sudo python run_exp.py --mode 0 --n 2 --b1 0 --b2 10000000
    ```
    - `mode`: 0 for Latency Priority, 1 for Bandwidth Constraint.
    - `n`: Number of subflows (for Mode 0).
    - `b1`, `b2`: Bandwidth range (for Mode 1).

## Scheduler Logic

The `mysche.progmp` scheduler supports two modes:

1.  **Latency Priority (Mode 0)**: Selects the top `n` subflows with the lowest RTT.
2.  **Bandwidth Constraint (Mode 1)**: Selects subflows greedily by bandwidth until the sum exceeds `b1` but stays under `b2` (logic adapted to greedy selection).

## License

MIT
