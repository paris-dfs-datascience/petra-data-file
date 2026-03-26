from fastapi import APIRouter

from src.schemas.feedback import FeedbackRequestSchema, FeedbackResponse
from src.services.feedback_service import FeedbackService


router = APIRouter(prefix="/feedback", tags=["feedback"])
service = FeedbackService()


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(data: FeedbackRequestSchema) -> FeedbackResponse:
    return service.append_feedback(data)
