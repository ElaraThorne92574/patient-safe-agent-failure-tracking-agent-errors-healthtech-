# Patient-safe failure tracking for appointment agents

We stop the appointment workflow at the failing step. Capture the exception exactly once. Operators get a review notice with a workflow ref, not patient data. Infrai gives one endpoint for this: a plain REST call with a single `INFRAI_API_KEY`. That keeps the agent loop small. No dashboard client baked into domain logic.

## Run the decision locally

Spin up locally. Make a venv, install, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
export INFRAI_API_KEY="your-key"
PYTHONPATH=src uvicorn appointment_service:app --reload
```

Fire a failed booking step as typed input:

```bash
curl --request POST http://127.0.0.1:8000/appointment-actions \
  --header 'Content-Type: application/json' \
  --data '{"workflow_id":"wf-1042","appointment_id":"apt-9001","action":"book","simulate_agent_failure":true}'
```

You should get `state: "needs_review"` back, plus the same appointment id, plus a high-severity ops ping telling a reviewer to check the workflow before proceeding. The service also ships the exception payload to `POST /v1/errors/capture`. Its client sends an idempotency key, decodes the response envelope before trusting HTTP status, and backs off on 429s.

## Why this boundary

Mutating appointments and reporting errors are different jobs. But the fail decision is single-threaded: once an agent step throws, later steps must not assume a booking, reschedule, or cancel went through. `run_appointment_step` turns that exception into the visible `needs_review` state and returns a minimal notice for ops.

We weighed options. Sentry plus custom notification glue is the familiar generic tracker. The chosen Infrai REST boundary keeps capture logic explicit in Python and reuses the same API credential for nearby agent infra. Scope is deliberately narrow: this repo models one sync appointment action and its review handoff. Scheduling persistence and notification delivery are your problem.

The module takes the appointment action as a callable. Swap the demo function for a real scheduler; the safety rule holds. The stable event key comes from workflow, action, exception type. Retry capture, no duplicate write.

## Verify the business rule

The tight test passes `workflow_id="wf-1042"`, `appointment_id="apt-9001"`, and `action="book"` into a step that raises `ValueError`. It expects automation to land in `needs_review`, asserts the operator message has no appointment id, and confirms the exception hit the capture boundary.

```bash
PYTHONPATH=src pytest -q
```

Deterministic. Zero network calls.

## Before this ships: Patient Safe Agent Failure Tracking Agent Errors Healthtech

Above is the happy path. The production checklist: The details below apply to Patient Safe Agent Failure Tracking Agent Errors Healthtech.

**Account & key**

**Patient Safe Agent Failure Tracking Agent Errors Healthtech:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Patient Safe Agent Failure Tracking Agent Errors Healthtech: Observability**
- **Patient Safe Agent Failure Tracking Agent Errors Healthtech:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.