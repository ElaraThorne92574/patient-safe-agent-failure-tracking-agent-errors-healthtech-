"""HTTP entry point for the appointment safety example."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict

from appointment_safety.infrai_errors import InfraiError, InfraiTransportError
from appointment_safety.workflow import AppointmentRequest, run_appointment_step

app = FastAPI(title="Appointment agent safety boundary")


class AppointmentBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    appointment_id: str
    action: str
    simulate_agent_failure: bool = False


class NotificationBody(BaseModel):
    workflow_id: str
    severity: str
    message: str


class AppointmentResponse(BaseModel):
    state: str
    appointment_id: str
    notification: NotificationBody | None = None


@app.post("/appointment-actions", response_model=AppointmentResponse)
def appointment_action(body: AppointmentBody) -> AppointmentResponse:
    if body.action not in {"book", "reschedule", "cancel"}:
        raise HTTPException(status_code=422, detail="Unsupported appointment action")

    request = AppointmentRequest(
        workflow_id=body.workflow_id,
        appointment_id=body.appointment_id,
        action=body.action,
    )

    def perform(_: AppointmentRequest) -> None:
        if body.simulate_agent_failure:
            raise RuntimeError("scheduling tool did not complete the action")

    try:
        result = run_appointment_step(request, perform)
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail=exc.detail) from exc
    except InfraiTransportError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return AppointmentResponse.model_validate(result, from_attributes=True)
