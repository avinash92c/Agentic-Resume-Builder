from typing import Optional, Any, Dict, List

from model import AgentResponse, AgentResponseData


def map_interrupt_data(interrupt_data: Optional[Dict[str, Any]]) -> Optional[AgentResponseData]:
    """Normalize interrupt payloads from different graphs into AgentResponseData.

    Accepts multiple interrupt shapes and returns a consistent AgentResponseData
    or None when no interrupt payload is provided.
    """
    if not interrupt_data or not isinstance(interrupt_data, dict):
        return None

    action = interrupt_data.get("action")

    # questions: support multiple possible keys
    questions: List[str] = []
    for qk in ("questions", "Question", "refinement_questions", "generated_questions"):
        v = interrupt_data.get(qk)
        if v:
            if isinstance(v, list):
                questions = [str(x) for x in v]
            else:
                # sometimes a newline-separated string
                questions = [s.strip() for s in str(v).split('\n') if s.strip()]
            break

    # draft: prefer latest element from 'drafts' list, else 'latest_draft' or 'draft'
    draft_val = None
    if "drafts" in interrupt_data and isinstance(interrupt_data.get("drafts"), list):
        drafts_list = interrupt_data.get("drafts")
        draft_val = drafts_list[-1] if drafts_list else None
    else:
        draft_val = interrupt_data.get("latest_draft") or interrupt_data.get("draft")

    # messages and refinement/approval prompts
    message = interrupt_data.get("message")
    refinement_question = None
    approval_question = interrupt_data.get("approval_question")

    if action == "request_refinement_feedback":
        # message field used for refinement prompt in some graphs
        refinement_question = message
        message = None

    return AgentResponseData(
        action=action,
        message=message,
        questions=questions,
        draft=draft_val,
        approval_question=approval_question,
        refinement_question=refinement_question,
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