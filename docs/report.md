# REST/JSON vs gRPC/protobuf: NS API benchmark

## Goal

In SIS #1 I chose REST/JSON for the NS API (`POST /v1/events`). In this benchmark I compare it with a gRPC/protobuf version of the same endpoint to check whether the choice holds: latency, throughput and payload size.

## Setup

- Both APIs call the same `AcceptEventUseCase`: idempotency check in PostgreSQL, write to Kafka with `acks=all`, save `event_id`. Only the transport differs.
- Each API: 1 container, 4 processes (uvicorn workers for REST, `SO_REUSEPORT` processes for gRPC), Kafka producer `linger_ms=5`.
- Kafka: 3 brokers (KRaft), replication factor 3, `min.insync.replicas=2`.
- PostgreSQL: 1 instance. Processors, workers and mock providers run in the background, as in a real system.
- Everything runs in one Podman VM: 7 vCPU, 16 GB RAM (MacBook Pro M1 Pro).

## Method

- Load generator: k6, run in a container inside the same network (no macOS port forwarding).
- Closed model: N virtual users (VUs), each sends the next request right after the previous response.
- Event: `pin_liked` for a random recipient out of 1000, unique `event_id` per request.
- VUs 1, 10, 50: 10 000 requests per run. VUs 100, 200: 100 000 requests per run (more stable).
- Payload size: the same 10 000 events serialized to JSON and protobuf, body only (no HTTP headers).

## Results

### Throughput and latency

| VUs | REST rps | gRPC rps | REST p50 / p99, ms | gRPC p50 / p99, ms |
|---|---|---|---|---|
| 1 | 117 | 117 | 7.9 / 15.6 | 7.8 / 15.5 |
| 10 | 816 | 814 | 11.3 / 25.7 | 11.3 / 25.0 |
| 50 | 2090 | 2269 | 21.7 / 57.2 | 20.3 / 49.7 |
| 100 | 2683 | 2470 | 32.7 / 106.3 | 36.0 / 117.2 |
| 200 | 3081 | 2963 | 56.7 / 190.4 | 59.2 / 209.9 |

No failed requests in any run.

![Throughput](images/throughput.png)

![Latency](images/latency.png)

### Payload size

| Format | Avg body size | Relative |
|---|---|---|
| JSON | 187 B | 100% |
| protobuf | 99 B | 53% |

Total client traffic for 100 000 requests: REST sent 32 MB, gRPC sent 16 MB.

![Payload size](images/payload_size.png)

## Analysis

- Latency and throughput of REST and gRPC are the same within run-to-run noise. On short runs gRPC was a bit faster, on long runs REST was a bit faster.
- Both reach the same ceiling of ~3000 rps per instance. The limit is shared dependencies (Kafka with `acks=all`, PostgreSQL, CPU of one VM), not the protocol.
- At 1 VU latency is ~8 ms, of which up to 5 ms is `linger_ms` batching. Under load batching pays off.
- protobuf is ~2x smaller. At the SIS #1 peak (9000 events/s) this is ~1.7 MB/s vs ~0.9 MB/s, which is negligible for an internal network.
- Earlier, with 1 process per API and no `uvloop`, gRPC was ~1.8x faster. That was the overhead of pure-Python HTTP handling in FastAPI, not of REST itself; it disappeared after scaling to 4 processes.

## Conclusion

I keep REST/JSON for the NS API:

- gRPC gives no latency or throughput gain at the SIS #1 load, only ~2x less traffic that is not a bottleneck.
- End-to-end delivery time (p99 < 5 s) is dominated by Kafka, the processor and providers (~250 ms), not by the input format.
- Events are stored in Kafka as JSON anyway, so the protobuf size gain is lost at the first hop.
- REST is simpler for producers: no generated code, easy debugging with `curl`, readable messages.

The benchmark also confirms the SIS #1 capacity estimate: one instance handles ~3000 events/s, so the 9000/s peak needs 5 instances at 60% utilization.

## Limitations

- All services share one VM, so absolute numbers are lower than on dedicated servers.
- One PostgreSQL instance instead of a sharded cluster; no Redis cache.
- Background pipeline load varies between runs, which adds noise of about +-10%.