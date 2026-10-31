import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

PROTOCOL_LABELS = {"rest": "REST / JSON", "grpc": "gRPC / protobuf"}
PROTOCOL_COLORS = {"rest": "#1f77b4", "grpc": "#ff7f0e"}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot benchmark results")
    parser.add_argument("--results-dir", type=Path, default=Path("benchmark_results"))
    parser.add_argument("--output-dir", type=Path, default=Path("docs/images"))
    return parser.parse_args()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def plot_throughput(results: dict, output_path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 5))
    for protocol, runs in results.items():
        vus = [run["vus"] for run in runs]
        throughput = [run["throughput_rps"] for run in runs]
        axis.plot(vus, throughput, marker="o", label=PROTOCOL_LABELS[protocol], color=PROTOCOL_COLORS[protocol])
    axis.set_xscale("log")
    axis.set_xticks([1, 10, 50, 100, 200], labels=["1", "10", "50", "100", "200"])
    axis.set_xlabel("Concurrent clients (VUs)")
    axis.set_ylabel("Throughput, requests/s")
    axis.set_title("Throughput: REST vs gRPC")
    axis.grid(True, alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def plot_latency(results: dict, output_path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 5))
    for protocol, runs in results.items():
        vus = [run["vus"] for run in runs]
        p50 = [run["p50_ms"] for run in runs]
        p99 = [run["p99_ms"] for run in runs]
        color = PROTOCOL_COLORS[protocol]
        axis.plot(vus, p50, marker="o", color=color, label=f"{PROTOCOL_LABELS[protocol]} p50")
        axis.plot(vus, p99, marker="s", linestyle="--", color=color, label=f"{PROTOCOL_LABELS[protocol]} p99")
    axis.set_xscale("log")
    axis.set_xticks([1, 10, 50, 100, 200], labels=["1", "10", "50", "100", "200"])
    axis.set_xlabel("Concurrent clients (VUs)")
    axis.set_ylabel("Latency, ms")
    axis.set_title("Latency: REST vs gRPC")
    axis.grid(True, alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def plot_payload_size(payload_sizes: dict, output_path: Path) -> None:
    labels = [PROTOCOL_LABELS["rest"], PROTOCOL_LABELS["grpc"]]
    sizes = [payload_sizes["json"]["avg_bytes"], payload_sizes["protobuf"]["avg_bytes"]]
    colors = [PROTOCOL_COLORS["rest"], PROTOCOL_COLORS["grpc"]]
    figure, axis = plt.subplots(figsize=(6, 5))
    bars = axis.bar(labels, sizes, color=colors)
    axis.bar_label(bars, labels=[f"{size:.0f} B" for size in sizes])
    axis.set_ylabel("Average request body size, bytes")
    axis.set_title("Payload size per event")
    axis.grid(True, axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def main() -> None:
    arguments = parse_arguments()
    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    k6_results = load_json(arguments.results_dir / "k6_results.json")
    payload_sizes = load_json(arguments.results_dir / "payload_size.json")
    plot_throughput(k6_results, arguments.output_dir / "throughput.png")
    plot_latency(k6_results, arguments.output_dir / "latency.png")
    plot_payload_size(payload_sizes, arguments.output_dir / "payload_size.png")


if __name__ == "__main__":
    main()