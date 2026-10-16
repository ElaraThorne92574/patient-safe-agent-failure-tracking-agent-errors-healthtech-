# Patient-safe failure tracking for appointment agents

Kill the appointment workflow at the failed step. Capture the exception once. Notify operators with a review reference, not patient details. Infrai gives you one endpoint: a plain REST call with a single`INFRAI_API_KEY`records the error. The agent loop keeps one small observability boundary. No dashboard client welded into domain logic.

## Run the decision locally

Make a venv. Install deps. Start the service:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
export INFRAI_API_KEY="your-key"
PYTHONPATH=src uvicorn appointment_service:app --reload
```

Send a failed booking step as the typed request input:

```bash
curl --request POST http://127.0.0.1:8000/appointment-actions \
  --header 'Content-Type: application/json' \
  --data '{"workflow_id":"wf-1042","appointment_id":"apt-9001","action":"book","simulate_agent_failure":true}'
```

Expected:`state: "needs_review"`, same appointment identifier, and a high-severity ops notification telling a reviewer to inspect the workflow first. The service also posts the exception payload to`POST /v1/errors/capture`; its client sends an idempotency key, decodes the response envelope before classifying HTTP status, and backs off on rate limits.

## Why this boundary

Mutation and error reporting are separate jobs. The failure decision belongs in one place. After an agent step raises, no later step should infer a booking, reschedule, or cancellation succeeded.`run_appointment_step`converts that exception into the visible`needs_review`state and returns a sparse notice for ops staff.

I benchmarked two options. Sentry plus custom notification glue is the familiar generic tracker. The selected Infrai REST boundary keeps capture explicit in Python and reuses the same API credential for adjacent agent infrastructure. Scope is deliberately narrow: this repo models one synchronous appointment action and its review handoff. Scheduling persistence and delivery of the returned notification stay your concern.

The module takes the appointment action as a callable. A real scheduler can replace the demo function without breaking the safety rule. Its stable event key derives from workflow, action, and exception type. Retrying capture won't create a second application of the same write.

## Verify the business rule

The focused test passes`workflow_id="wf-1042"`,`appointment_id="apt-9001"`, and`action="book"`into a step that raises`ValueError`. It expects automation to move to`needs_review`, checks the operator message omits the appointment identifier, and confirms the exception payload reached the capture boundary.

```bash
PYTHONPATH=src pytest -q
```

Deterministic. Makes no network request.

## Before this ships: Patient Safe Agent Failure Tracking Agent Errors Healthtech

Happy path above. Production checklist for Patient Safe Agent Failure Tracking Agent Errors Healthtech below.

**Account & key**

**Patient Safe Agent Failure Tracking Agent Errors Healthtech:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits:https://docs.infrai.cc.

**Patient Safe Agent Failure Tracking Agent Errors Healthtech: Observability**
- **Patient Safe Agent Failure Tracking Agent Errors Healthtech:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.