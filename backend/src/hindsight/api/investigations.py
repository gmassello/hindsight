from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from hindsight.agent.context import Ctx
from hindsight.agent.orchestrator import commit_and_learn, investigate
from hindsight.datahub.mcp_client import DataHubMCP
from hindsight.models import InvestigationState, TimelineEvent

router = APIRouter(prefix="/investigations")

_store: dict[str, InvestigationState] = {}
_started: set[str] = set()


class CreateRequest(BaseModel):
    text: str


class CommitResponse(BaseModel):
    state: InvestigationState
    events: list[TimelineEvent]


def _get(investigation_id: str) -> InvestigationState:
    state = _store.get(investigation_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return state


@router.post("")
def create(request: CreateRequest) -> InvestigationState:
    state = InvestigationState.new(request.text)
    _store[state.id] = state
    return state


@router.get("/{investigation_id}")
def get(investigation_id: str) -> InvestigationState:
    return _get(investigation_id)


@router.get("/{investigation_id}/stream")
async def stream(investigation_id: str) -> EventSourceResponse:
    state = _get(investigation_id)
    if state.status != "investigating" or investigation_id in _started:
        raise HTTPException(
            status_code=409,
            detail=f"Investigation already started (status: {state.status})",
        )
    _started.add(investigation_id)

    async def generator():
        try:
            async with DataHubMCP() as datahub:
                ctx = Ctx(state=state, datahub=datahub)
                async for event in investigate(ctx):
                    yield {"event": event.kind, "data": event.model_dump_json()}
            yield {"event": "state", "data": state.model_dump_json()}
        except Exception as exc:
            state.status = "failed"
            yield {
                "event": "agent_error",
                "data": TimelineEvent(
                    phase="orchestrator", kind="error", message=str(exc)
                ).model_dump_json(),
            }

    return EventSourceResponse(generator())


@router.post("/{investigation_id}/approve")
async def approve(investigation_id: str) -> CommitResponse:
    state = _get(investigation_id)
    if state.status != "awaiting_approval":
        raise HTTPException(status_code=409, detail=f"Investigation is {state.status}")
    state.status = "committing"
    events: list[TimelineEvent] = []
    async with DataHubMCP() as datahub:
        ctx = Ctx(state=state, datahub=datahub)
        async for event in commit_and_learn(ctx):
            events.append(event)
    return CommitResponse(state=state, events=events)


@router.post("/{investigation_id}/reject")
def reject(investigation_id: str) -> InvestigationState:
    state = _get(investigation_id)
    if state.status != "awaiting_approval":
        raise HTTPException(status_code=409, detail=f"Investigation is {state.status}")
    state.status = "rejected"
    return state
