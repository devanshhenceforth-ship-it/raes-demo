from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from .queue import get_job_queue
from ..helper import get_result_queue

router = APIRouter(
    prefix="/inspection",
    tags=["Inspection SSE"],
)


@router.get("/events/{room_id}")
async def inspection_events(room_id: str):
    """
    GET: SSE stream for a given job
    """
    queue = get_job_queue(room_id)

    async def event_generator():
        while True:
            data = await queue.get()
            yield {"event": "update", "data": data}

    return EventSourceResponse(event_generator())
