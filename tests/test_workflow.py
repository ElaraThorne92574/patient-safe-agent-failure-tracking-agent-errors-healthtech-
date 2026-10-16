from appointment_safety.workflow import AppointmentRequest, run_appointment_step


def test_failed_booking_pauses_automation_and_emits_safe_notification() -> None:
    captures: list[dict] = []
    request = AppointmentRequest(
        workflow_id="wf-1042",
        appointment_id="apt-9001",
        action="book",
    )

    def fail(_: AppointmentRequest) -> None:
        raise ValueError("calendar slot changed")

    result = run_appointment_step(
        request,
        fail,
        capture=lambda **payload: captures.append(payload) or {"event_id": "evt-1"},
    )

    assert result.state == "needs_review"
    assert result.notification is not None
    assert result.notification.workflow_id == "wf-1042"
    assert "apt-9001" not in result.notification.message
    assert "ValueError: calendar slot changed" in captures[0]["exception"]
    assert captures[0]["idempotency_key"]
