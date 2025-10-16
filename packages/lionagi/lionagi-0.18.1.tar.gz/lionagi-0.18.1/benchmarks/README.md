Minimal concurrency benchmarks

This folder contains a lightweight benchmark runner for lionagi.ln.concurrency.
It establishes a baseline for core patterns to help catch regressions.

How to run (concurrency)

- Asyncio backend (default):
  - `python -m benchmarks.concurrency_bench`
- Trio backend:
  - `python -m benchmarks.concurrency_bench --backend trio`

Options

- `--backend {asyncio,trio}`: Select async backend (default: asyncio)
- `--repeat N`: Repeat each scenario N times and report aggregates (default: 3)
- `--json`: Also print JSON to stdout (besides saving to file)
- `--output PATH`: Save results JSON to a custom path
- `--compare BASELINE.json`: Compare against a previous run and show deltas

How to run (ln functions)

- Asyncio backend (default):
  - `python -m benchmarks.ln_bench`
- Trio backend:
  - `python -m benchmarks.ln_bench --backend trio`

Options are the same as the concurrency runner.

Results

- Results are saved under `benchmarks/results/<timestamp>-<backend>.json`
  (concurrency) and `benchmarks/results/ln-<timestamp>-<backend>.json` (ln
  functions) by default.
- Each scenario reports min/mean/median/max (seconds) over the configured
  repeats.

Scenarios (initial set)

- gather_100_yield: 100 tasks, each yields once (sleep 0)
- bounded_map_2000_limit_100: 2000 items, async no-op mapper, limit=100
- completion_stream_1000_limit_100: 1000 awaitables streamed with limit=100
- race_first_completion_10: 10 tasks where one completes immediately
- cancel_propagation_500: 500 tasks; one fails quickly to trigger cancellation
- taskgroup_start_1000_noop: start 1000 short-lived tasks

Notes

- Fuzzy utilities benches are available:
  - `python -m benchmarks.fuzzy_bench` (JSON parsing, extraction, key matching)
  - Outputs to `benchmarks/results/fuzzy-<timestamp>.json`
- These are micro-benchmarks intended to detect relative changes, not absolute
  throughput.
- Run on a quiet machine for less noisy results. Prefer CI runners for
  consistency.
