"""Decision boundary for failures inside an appointment agent loop."""

from __future__ import annotations

import hashlib
import traceback
from dataclasses import dataclass
from typing import Callable, Literal

from .infrai_errors import capture_exception


@dataclass(frozen=True)
class AppointmentRequest:
    workflow_id: str
    appointment_id: str
    action: Literal["book", "reschedule", "cancel"]


@dataclass(frozen=True)
class OperationalNotification:
    workflow_id: str
    severity: Literal["high"]
    message: str


@dataclass(frozen=True)
class WorkflowResult:
    state: Literal["completed", "needs_review"]
    appointment_id: str
    notification: OperationalNotification | None = None


def run_appointment_step(
    request: AppointmentRequest,
    perform: Callable[[AppointmentRequest], None],
    *,
    capture: Callable[..., dict] = capture_exception,
) -> WorkflowResult:
    """Run one appointment action; failures pause automation for human review."""
    try:
        perform(request)
        return WorkflowResult(state="completed", appointment_id=request.appointment_id)
    except Exception as exc:
        event_key = hashlib.sha256(
            f"{request.workflow_id}:{request.action}:{type(exc).__name__}".encode()
        ).hexdigest()
        capture(
            exception=traceback.format_exc(),
            idempotency_key=event_key,
        )
        return WorkflowResult(
            state="needs_review",
            appointment_id=request.appointment_id,
            notification=OperationalNotification(
                workflow_id=request.workflow_id,
                severity="high",
                message="Appointment automation paused; review the workflow before continuing.",
            ),
        )
