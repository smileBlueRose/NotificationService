import argparse
import json
import statistics
from pathlib import Path

from google.protobuf import struct_pb2, timestamp_pb2

from benchmark.sample_events import build_sample_events
from common.models import Event
from event_contract import events_pb2


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="JSON vs protobuf payload size")
    parser.add_argument("--events", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def to_json_bytes(event: Event) -> bytes:
    return event.model_dump_json().encode()


def to_protobuf_bytes(event: Event) -> bytes:
    created_at = timestamp_pb2.Timestamp()
    created_at.FromDatetime(event.created_at)
    payload = struct_pb2.Struct()
    payload.update(event.payload)
    message = events_pb2.Event(
        event_id=str(event.event_id),
        event_type=events_pb2.EventType.Value(f"EVENT_TYPE_{event.event_type.value.upper()}"),
        recipient_id=event.recipient_id,
        created_at=created_at,
        payload=payload,
    )
    return message.SerializeToString()


def describe_sizes(sizes: list[int]) -> dict[str, float]:
    return {
        "avg_bytes": round(statistics.mean(sizes), 1),
        "min_bytes": min(sizes),
        "max_bytes": max(sizes),
    }


def main() -> None:
    arguments = parse_arguments()
    events = build_sample_events(arguments.events, arguments.seed)
    json_sizes = [len(to_json_bytes(event)) for event in events]
    protobuf_sizes = [len(to_protobuf_bytes(event)) for event in events]

    json_average = statistics.mean(json_sizes)
    protobuf_average = statistics.mean(protobuf_sizes)
    summary = {
        "events": arguments.events,
        "json": describe_sizes(json_sizes),
        "protobuf": describe_sizes(protobuf_sizes),
        "protobuf_to_json_ratio": round(protobuf_average / json_average, 3),
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()