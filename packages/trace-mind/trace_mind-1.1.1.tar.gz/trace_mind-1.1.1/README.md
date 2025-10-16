# TraceMind — AI MAPE-K Autonomous Agent Framework

TraceMind is a lightweight, event-sourced **autonomous agent runtime** that follows the
**MAPE-K** loop: **Monitor → Analyze → Plan → Execute** over shared **Knowledge**.

- **Event-Sourced Core** — every state change is an append-only fact (auditable by design).
- **Static Flow Engine** — declarative flows (YAML/JSON) exportable to DOT/JSON for graphs.
- **Policy via MCP** — select/update arms locally or over JSON-RPC with timeout & safe fallback.
- **Smart Layer** — summarize / diagnose / plan / reflect with trace-linked spans.
- **Ops-Ready** — REST `/api/*`, Prometheus `/metrics`, health `/healthz` `/readyz`.

---

| Client + Server | Digital Twin | Autonomous Agent |
| --- | --- | --- |
| • Proxy / adapter<br>• SIP / WebSocket<br>• Hide protocol complexity | • Mirror of entity<br>• Presence + feedback<br>• IoT / telecom<br>• State visualisation<br>• Simulation / feedback | • Observer<br>• Executor<br>• Collaborator<br>• AI-driven autonomy<br>• Coordination in MAS |
| **Value:** simplify access | **Value:** insight + control | **Value:** autonomy + learning |

---

## ✨ Features

* **Event Sourcing Core**: append-only event store powered by the Binary Segment Log (`tm/storage/binlog.py`). JSONL and SQLite remain optional adapters planned for future expansion.
* **DDD Structure**: clear separation of domain, application, and infrastructure layers.
* **Pipeline Engine**: field-driven processing (Plan → Rule → Step), statically analyzable.
* **Tracing & Reflection**: every step produces auditable spans.
* **Smart Layer**:

  * Summarize: human-readable summaries of recent events.
  * Diagnose: heuristic anomaly detection with suggested actions.
  * Plan: goal → steps → optional execution.
  * Reflect: postmortem reports and threshold recommendations.
* **Visualization**:

  * Static: export DOT/JSON diagrams of flows.
  * Dynamic: SSE dashboard with live DAG and insights panel.
* **Protocols**:

  * MCP (Model Context Protocol) integration (JSON-RPC 2.0) – see the
    [latest specification](https://modelcontextprotocol.io/specification/latest)
    and the [community GitHub org](https://github.com/modelcontextprotocol).
    Example flow recipe:
    ```python
    from tm.recipes.mcp_flows import mcp_tool_call

    spec = mcp_tool_call("files", "list", ["path"])
    runtime.register(_SpecFlow(spec))
    ```
* **Interfaces**:

  * REST API: `/api/commands/*`, `/api/query/*`, `/agent/chat`.
  * Metrics: `/metrics` (Prometheus format).
  * Health checks: `/healthz`, `/readyz`.

---

## 📂 Architecture (ASCII Overview)

```
                +----------------+
                |   REST / CLI   |
                +----------------+
                         |
                    [Commands]
                         v
                +----------------+
                |  App Service   |
                +----------------+
                         |
                  +------+------+
                  |             |
             [Event Store]   [Event Bus]
                  |             |
          +-------+        +----+-----------------+
          |                |                      |
     [Projections]   [Pipeline Engine]      [Smart Layer]
                          |              (Summarize/Diagnose/Plan/Reflect)
                          v
                      [Trace Store]
```

---

## 📚 Documentation

- [Flow & policy recipes](docs/recipes-v1.md)
- [Helpers reference](docs/helpers.md)
- [Policy lifecycle & MCP integration](docs/policy.md)
- [Storage configuration](docs/storage.md)
- [Validation & simulation workflows](docs/validation.md)

### Scale & Reliability

- [Scale & Reliability guide](docs/scale-and-reliability.md)
- [Queue retries & DLQ](docs/howto/retries_dlq.md)

### Safety & Governance

- [Governance overview](docs/governance.md)
- [Guardrails](docs/guard.md)
- [Human approvals](docs/hitl.md)

---

## 🚀 Quick Start

```bash
# Install (use venv if you like)
pip install -U "git+https://github.com/RaphaelYu/TraceMind.git@v1.0.4"

# Version & pipeline health
tm --version
tm pipeline analyze

# Scaffold & run a minimal flow
tm init demo
cd demo
tm run flows/hello.yaml -i '{"name":"world"}'

# Validate and export the flow graph
mkdir -p out
tm pipeline export-dot --out-rules-steps out/rules.dot --out-step-deps out/steps.dot

# Policy: list / verify / (optional) update
python3 - <<'PY'
import asyncio
from tm.policy.adapter import PolicyAdapter
from tm.policy.local_store import LocalPolicyStore


async def main():
    arms = {
        "maint.default": {"threshold": 0.72},
        "maint.backup": {"threshold": 0.6},
    }
    store = LocalPolicyStore(arms=arms)
    adapter = PolicyAdapter(mcp=None, local=store)
    print("arms:", await adapter.list_arms())
    baseline = await adapter.get("maint.default")
    print("before:", baseline)
    updated = await adapter.update("maint.default", {"threshold": 0.85})
    print("after:", updated)


asyncio.run(main())
PY
```

### DSL Tooling (WDL / PDL)

TraceMind ships a DSL layer for workflows (WDL) and policies (PDL). Install the optional extras once (`pip install networkx PyYAML`) and you can lint/plan/compile/testgen directly from the repo:

```bash
# Lint individual files or directories
python -m tm.cli dsl lint examples/dsl/opcua

# Compile to runtime artifacts (writes out/flows + out/policies + out/triggers.yaml)
python -m tm.cli dsl compile examples/dsl/opcua --out out/dsl --force

# Generate coverage fixtures (≥6 cases per workflow by default)
python -m tm.cli dsl testgen examples/dsl/opcua --out examples/fixtures

# Validate trigger configuration
python -m tm.cli triggers validate out/dsl/triggers.yaml

# Launch daemon with triggers (requires networkx / croniter)
export TM_ENABLE_DAEMON=1
python -m tm.cli daemon start --enable-triggers --triggers-config out/dsl/triggers.yaml --queue-dir tmp/queue --idempotency-dir tmp/idempotency --workers 1

# Run the compiled flow with the example inputs
python -m tm.cli run out/dsl/flows/plant-monitor.yaml -i '@examples/dsl/opcua/input.json'
```

For CI-style smoke tests, use `scripts/validate_dsl_examples.sh` which performs the lint/plan/compile/testgen/run loop end to end (it respects `$PYTHON` and checks for optional dependencies such as `networkx`). The generated artifacts carry source metadata so downstream tools can trace decisions back to DSL files.

### Always-on Agent quickstart

Reuse the copy/paste examples in the validation guide to keep agents continuously self-checking:

- [`docs/validation.md`](docs/validation.md) — `tm flow lint`, `tm flow plan`, `tm validate`, `tm simulate`.
- [`scripts/validate_examples.sh`](scripts/validate_examples.sh) — end-to-end smoke test that runs as part of CI.

Need to configure persistence for production?  See [`docs/storage.md`](docs/storage.md) for KStore URLs and fallback behaviour.

### Background daemon (opt-in)

TraceMind can run flows in the background via a daemon + queue worker loop. Enable it explicitly:

```bash
export TM_ENABLE_DAEMON=1
export TM_FILE_QUEUE_V2=1  # recommended for durable queue semantics
```

High-level workflow:

```bash
# Start the daemon (spawns workers under the hood)
tm daemon start --queue-dir data/queue --idempotency-dir data/idempotency

# Enqueue work without blocking
tm run flows/hello.yaml --detached -i '{"name":"async"}'

# Check status (human readable or JSON)
tm daemon ps
tm daemon ps --json | jq .

# Stop the daemon gracefully (forces after timeout unless --no-force)
tm daemon stop

# Start the daemon with triggers enabled
tm daemon start --enable-triggers --triggers-config triggers.yaml
```

Triggers can also run without the daemon:

```bash
tm triggers init             # scaffold config
tm triggers validate         # lint configuration
tm triggers run --config triggers.yaml
```

See [`docs/daemon.md`](docs/daemon.md) for configuration details, troubleshooting tips, and a deeper explanation of queue/idempotency directory layout. CI runs a smoke script (`scripts/daemon_smoke.sh`) to ensure the loop stays healthy. Trigger design, adapter reference, and templates live in [`docs/triggers.md`](docs/triggers.md).

### Run in container

```bash
docker build -t trace-mind ./docker

docker run --rm -it \
  --read-only \
  -v $(pwd)/data:/data \
  -p 8080:8080 \
  trace-mind
```


### Scale & Reliability demo

See the [Scale & Reliability guide](docs/scale-and-reliability.md) for full context. The commands below can be pasted into a shell to exercise the worker pool, queue stats, and DLQ tooling.

```bash
# Start workers
TM_LOG=info tm workers start -n 4 --queue file --lease-ms 30000 &

# Enqueue 1000 CPU-light tasks
for i in {1..1000}; do tm enqueue flows/hello.yaml -i '{"name":"w'$i'"}'; done

# Live queue stats
tm queue stats

# Retry/DLQ demo — simulate failures by input flag/env within your step
export FAIL_RATE=0.05
# (run some tasks…)

tm dlq ls | head        # Inspect
# Requeue a subset by id/prefix/predicate (implementation-specific)
tm dlq requeue <task-id>

# Graceful drain
tm workers stop
```

---

## 🧩 Roadmap

* [ ] More connectors (file bridge, http bridge, kafka bridge)
* [ ] Richer dashboard with interactive actions
* [ ] Adaptive thresholds in Reflector
* [ ] Optional LLM integration for natural summaries

---

## 📜 License

MIT (for personal and experimental use)

Quickstart:
tm init demo --template minimal
cd demo && tm run flows/hello.yaml -i '{"name":"world"}'
More details: docs/quickstart.md
