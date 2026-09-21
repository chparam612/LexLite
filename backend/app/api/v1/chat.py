from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.conversation import MessageResponse, CitationResponse
from app.services.chat_service import ChatService

router = APIRouter(tags=["Chat & Citations"])
chat_service = ChatService()


class DirectChatRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Legal query to analyze against documents.")
    conversation_id: Optional[str] = Field(None, description="Optional existing conversation ID.")
    document_ids: Optional[List[str]] = Field(default_factory=list, description="Target document IDs.")


@router.post("/chat", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def direct_chat(
    payload: DirectChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Direct Chat Endpoint (Phase 9 capability).
    Executes question answering, auto-initiating a session if conversation_id is omitted.
    """
    conv_id = payload.conversation_id
    if not conv_id:
        conv = chat_service.create_conversation(
            db=db,
            user=current_user,
            title="Legal Research",
            document_ids=payload.document_ids or []
        )
        conv_id = conv.id

    return chat_service.send_message(
        db=db,
        user=current_user,
        conversation_id=conv_id,
        content=payload.content
    )


@router.get("/messages/{message_id}/citations", response_model=List[CitationResponse], status_code=status.HTTP_200_OK)
def get_message_citations(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch evidentiary citations for an assistant message (Phase 9 capability).
    """
    return chat_service.get_message_citations(
        db=db,
        user=current_user,
        message_id=message_id
    )
