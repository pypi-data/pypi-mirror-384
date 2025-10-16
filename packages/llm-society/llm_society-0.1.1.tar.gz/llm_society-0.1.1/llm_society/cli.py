#!/usr/bin/env python3
import argparse
from importlib import resources
from typing import Dict, Any, List

from llm_society.config import load_config, DEFAULTS
from llm_society.simulation import run_simulation


def write_example_config(dest_path: str) -> None:
    with resources.files("llm_society").joinpath("data/example.yaml").open("rb") as rf:
        data = rf.read()
    with open(dest_path, "wb") as wf:
        wf.write(data)


def _parse_seeds(val: str) -> List[int]:
    return [int(x) for x in val.split(",") if x.strip() != ""]


def main() -> None:
    p = argparse.ArgumentParser(description="Run LLM Society simulation")
    # Config IO
    p.add_argument("--config", type=str, help="Path to YAML/JSON config file", default=None)
    p.add_argument("--write-example-config", type=str, metavar="PATH", help="Write packaged example config to PATH and exit")
    # Unified API-style flags (all optional; override config/defaults if provided)
    p.add_argument("--information", type=str, help="Information text (claim) to simulate", default=None)
    p.add_argument("--n", type=int, help="Number of agents", default=None)
    p.add_argument("--degree", type=int, help="Mean degree (edge_mean_degree)", default=None)
    p.add_argument("--rounds", type=int, help="Number of rounds", default=None)
    p.add_argument("--depth", type=float, help="Conversation depth intensity [0-1]", default=None)
    p.add_argument("--depth-max", type=int, help="Max conversation turns per pair", default=None)
    p.add_argument("--edge-frac", type=float, help="Fraction of edges sampled per round", default=None)
    p.add_argument("--seeds", type=str, help="Comma-separated seed node ids, e.g. 0,1,2", default=None)
    p.add_argument("--seed-belief", type=float, help="Initial belief for seed nodes [0-1]", default=None)
    p.add_argument("--talk-prob", type=float, help="Probability a sampled edge talks about the information [0-1]", default=None)
    p.add_argument("--mode", type=str, help="Contagion mode: llm|simple|complex", default=None)
    p.add_argument("--complex-k", type=int, help="Threshold k for complex contagion", default=None)
    p.add_argument("--stop-when-stable", action="store_true", help="Stop early when stable")
    p.add_argument("--stability-tol", type=float, help="Stability tolerance", default=None)
    p.add_argument("--rng", type=int, help="Random seed", default=None)
    p.add_argument("--api-key-file", type=str, help="Path to API key file", default=None)
    p.add_argument("--model", type=str, help="Model name for LLM calls", default=None)

    args = p.parse_args()

    if args.write_example_config:
        write_example_config(args.write_example_config)
        print(f"Wrote example config to {args.write_example_config}")
        return

    # Base config: from file if provided, else defaults
    if args.config:
        cfg: Dict[str, Any] = load_config(args.config)
    else:
        cfg = dict(DEFAULTS)

    # Apply overrides from flags if provided
    if args.information is not None:
        cfg["information_text"] = args.information
    if args.n is not None:
        cfg["n"] = int(args.n)
    if args.degree is not None:
        cfg["edge_mean_degree"] = int(args.degree)
    if args.rounds is not None:
        cfg["rounds"] = int(args.rounds)
    if args.depth is not None:
        cfg["depth"] = float(args.depth)
    if args.depth_max is not None:
        cfg["max_convo_turns"] = int(args.depth_max)
    if args.edge_frac is not None:
        cfg["edge_sample_frac"] = float(args.edge_frac)
    if args.seeds is not None:
        cfg["seed_nodes"] = _parse_seeds(args.seeds)
    if args.seed_belief is not None:
        cfg["seed_belief"] = float(args.seed_belief)
    if args.talk_prob is not None:
        cfg["talk_information_prob"] = float(args.talk_prob)
    if args.mode is not None:
        cfg["contagion_mode"] = str(args.mode)
    if args.complex_k is not None:
        cfg["complex_threshold_k"] = int(args.complex_k)
    if args.stop_when_stable:
        cfg["stop_when_stable"] = True
    if args.stability_tol is not None:
        cfg["stability_tol"] = float(args.stability_tol)
    if args.rng is not None:
        cfg["rng_seed"] = int(args.rng)
    if args.api_key_file is not None:
        cfg["api_key_file"] = str(args.api_key_file)
    if args.model is not None:
        cfg["model"] = str(args.model)

    # Validate required information
    if not str(cfg.get("information_text", "")).strip():
        p.error("--information is required unless provided in --config")

    result = run_simulation(cfg)
    history = result["history"]
    print(f"Rounds: {len(history) - 1}")
    print(f"Round 0 summary: {history[0]['summary']}")
    print(f"Final coverage: {len(history[-1]['coverage'])}")


if __name__ == "__main__":
    main()


