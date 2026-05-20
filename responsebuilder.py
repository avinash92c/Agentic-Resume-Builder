from model import AgentResponse, AgentResponseData

def map_interrupt_data(interrupt_data: dict) -> AgentResponseData:

    return AgentResponseData(
        questions=interrupt_data.get("questions", []),
        draft=interrupt_data.get("drafts"),
        approval_question=interrupt_data.get("approval_question"),
        refinement_question=interrupt_data.get("refinement_question"),
    )

def build_agent_response(
    *,
    thread_id: str,
    stage: str,
    complete: bool = False,
    message: str | None = None,
    questions: list[str] | None = None,
    draft: str | None = None,
    refinement_question: str | None = None,
):
    return AgentResponse(
        thread_id=thread_id,
        stage=stage,
        complete=complete,
        data=AgentResponseData(
            message=message,
            questions=questions or [],
            refinement_question=refinement_question,
            draft=draft,
        ),
    )

def map_psg_state_to_response(state, thread_id):

    stage = state.get("current_stage", "")

    if stage == "awaiting_answers":
        return build_agent_response(
            thread_id=thread_id,
            stage=stage,
            questions=state.get("generated_questions", []),
        )

    if stage in [
        "pending_review",
        "pending_refinement_review"
    ]:
        drafts = state.get("drafts", [])

        latest_draft = drafts[-1] if drafts else ""

        return build_agent_response(
            thread_id=thread_id,
            stage=stage,
            draft=latest_draft,
            questions=[
                "Review the draft and provide approval"
            ],
        )

    if stage == "Completed":
        drafts = state.get("drafts", [])

        latest_draft = drafts[-1] if drafts else ""

        return build_agent_response(
            thread_id=thread_id,
            stage="completed",
            complete=True,
            message="Professional summary completed successfully.",
            draft=latest_draft,
        )

    return build_agent_response(
        thread_id=thread_id,
        stage="unknown",
        message="Unknown graph state",
    )