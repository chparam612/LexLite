from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationDetailResponse,
    MessageCreate,
    MessageResponse
)
from app.services.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new legal research conversation with optional attached documents."""
    return chat_service.create_conversation(
        db=db,
        user=current_user,
        title=payload.title,
        document_ids=payload.document_ids
    )


@router.get("", response_model=List[ConversationResponse])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all conversations for the authenticated user."""
    return chat_service.list_conversations(db=db, user=current_user)


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get conversation details, attached documents, and message history."""
    return chat_service.get_conversation_detail(
        db=db,
        user=current_user,
        conversation_id=conversation_id
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a conversation and all associated messages and citations."""
    chat_service.delete_conversation(
        db=db,
        user=current_user,
        conversation_id=conversation_id
    )
    return None


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def post_message(
    conversation_id: str,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a question, execute retrieval, and receive a grounded answer with citations."""
    return chat_service.send_message(
        db=db,
        user=current_user,
        conversation_id=conversation_id,
        content=payload.content
    )
