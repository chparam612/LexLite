import uuid
import time
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationDocument, Message
from app.models.citation import Citation, AnswerClaim, ClaimEvidence
from app.models.document import Document
from app.models.user import User
from app.core.exceptions import LegalAIException
from app.services.retrieval_service import RetrievalService
from app.services.generation_service import GenerationService
from app.schemas.conversation import (
    ConversationResponse,
    ConversationDetailResponse,
    MessageResponse,
    CitationResponse,
    ClaimResponse,
    ProcessingDetails
)


class ChatService:
    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        generation_service: Optional[GenerationService] = None
    ):
        self.retrieval_service = retrieval_service or RetrievalService()
        self.generation_service = generation_service or GenerationService()

    def create_conversation(
        self,
        db: Session,
        user: User,
        title: Optional[str] = None,
        document_ids: Optional[List[str]] = None
    ) -> ConversationResponse:
        conv_id = str(uuid.uuid4())
        conv = Conversation(
            id=conv_id,
            user_id=user.id,
            title=title or "Legal Research"
        )
        db.add(conv)

        valid_doc_ids: List[str] = []
        if document_ids:
            # Verify document ownership
            owned_docs = (
                db.query(Document)
                .filter(Document.id.in_(document_ids), Document.owner_id == user.id)
                .all()
            )
            for d in owned_docs:
                cd = ConversationDocument(conversation_id=conv_id, document_id=d.id)
                db.add(cd)
                valid_doc_ids.append(d.id)

        db.commit()
        db.refresh(conv)

        return ConversationResponse(
            id=conv.id,
            title=conv.title,
            document_ids=valid_doc_ids,
            created_at=conv.created_at,
            updated_at=conv.updated_at
        )

    def list_conversations(self, db: Session, user: User) -> List[ConversationResponse]:
        convs = (
            db.query(Conversation)
            .filter_by(user_id=user.id)
            .order_by(Conversation.updated_at.desc())
            .all()
        )
        result = []
        for c in convs:
            doc_ids = [d.document_id for d in c.documents]
            result.append(
                ConversationResponse(
                    id=c.id,
                    title=c.title,
                    document_ids=doc_ids,
                    created_at=c.created_at,
                    updated_at=c.updated_at
                )
            )
        return result

    def get_conversation_detail(self, db: Session, user: User, conversation_id: str) -> ConversationDetailResponse:
        conv = db.query(Conversation).filter_by(id=conversation_id, user_id=user.id).first()
        if not conv:
            raise LegalAIException("Conversation not found", code="CONVERSATION_NOT_FOUND", status_code=404)

        doc_ids = [d.document_id for d in conv.documents]

        # Fetch messages
        messages_db = (
            db.query(Message)
            .filter_by(conversation_id=conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )

        message_responses = []
        for m in messages_db:
            cits = [
                CitationResponse(
                    id=c.id,
                    chunk_id=c.chunk_id,
                    page_number=c.page_number,
                    section_label=c.section_label,
                    quoted_text=c.quoted_text,
                    citation_order=c.citation_order,
                    document_title=c.chunk.version.document.title if c.chunk and c.chunk.version else None
                )
                for c in m.citations
            ]
            claims = [
                ClaimResponse(
                    id=cl.id,
                    claim_text=cl.claim_text,
                    claim_type=cl.claim_type,
                    support_status=cl.support_status
                )
                for cl in m.claims
            ]
            message_responses.append(
                MessageResponse(
                    id=m.id,
                    conversation_id=m.conversation_id,
                    role=m.role,
                    content=m.content,
                    model_name=m.model_name,
                    citations=cits,
                    claims=claims,
                    created_at=m.created_at
                )
            )

        return ConversationDetailResponse(
            id=conv.id,
            title=conv.title,
            document_ids=doc_ids,
            messages=message_responses,
            created_at=conv.created_at,
            updated_at=conv.updated_at
        )

    def delete_conversation(self, db: Session, user: User, conversation_id: str) -> bool:
        conv = db.query(Conversation).filter_by(id=conversation_id, user_id=user.id).first()
        if not conv:
            raise LegalAIException("Conversation not found", code="CONVERSATION_NOT_FOUND", status_code=404)
        db.delete(conv)
        db.commit()
        return True

    def send_message(
        self,
        db: Session,
        user: User,
        conversation_id: str,
        content: str
    ) -> MessageResponse:
        """
        Execute RAG workflow for a message:
        1. Store user message
        2. Retrieve relevant document chunks
        3. Synthesize grounded answer
        4. Store assistant message, citations, claims, and audit logs
        """
        conv = db.query(Conversation).filter_by(id=conversation_id, user_id=user.id).first()
        if not conv:
            raise LegalAIException("Conversation not found", code="CONVERSATION_NOT_FOUND", status_code=404)

        clean_content = content.strip()
        if not clean_content:
            raise LegalAIException("Message content cannot be empty", code="EMPTY_MESSAGE", status_code=400)

        # 1. Store User Message
        user_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            role="user",
            content=clean_content
        )
        db.add(user_msg)
        conv.updated_at = datetime.now(timezone.utc)
        db.commit()

        # 2. Hybrid Retrieval (Dense + Keyword + RRF + Rerank + Expansion)
        doc_ids = [d.document_id for d in conv.documents] if conv.documents else None

        t0 = time.time()
        hits = self.retrieval_service.hybrid_search(
            db=db,
            user_id=user.id,
            query=clean_content,
            document_ids=doc_ids,
            top_k=5
        )
        latency_ms = round((time.time() - t0) * 1000, 2)

        # 3. Grounded Answer Synthesis
        grounded_resp = self.generation_service.generate_grounded_answer(
            query=clean_content,
            hits=hits
        )

        # 4. Store Assistant Message
        assistant_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            role="assistant",
            content=grounded_resp.answer,
            model_name=self.generation_service.model_name
        )
        db.add(assistant_msg)
        db.flush()

        # 5. Record Retrieval Run for auditability
        self.retrieval_service.record_retrieval_run(
            db=db,
            message_id=assistant_msg.id,
            query=clean_content,
            hits=hits,
            retrieval_method="hybrid",
            latency_ms=latency_ms
        )

        # 6. Record Citations and Claims
        claim_records: List[AnswerClaim] = []
        evidence_records: List[ClaimEvidence] = []
        citation_records: List[Citation] = []
        citation_responses: List[CitationResponse] = []

        for idx, claim_data in enumerate(grounded_resp.claims, start=1):
            claim_rec = AnswerClaim(
                id=str(uuid.uuid4()),
                message_id=assistant_msg.id,
                claim_text=claim_data.claim_text,
                claim_type="document_fact",
                support_status=claim_data.support_status
            )
            db.add(claim_rec)
            claim_records.append(claim_rec)
            db.flush()

            # Create claim evidence
            evidence = ClaimEvidence(
                id=str(uuid.uuid4()),
                claim_id=claim_rec.id,
                chunk_id=claim_data.chunk_id,
                entailment_score=1.0,
                evidence_type="direct_quote"
            )
            db.add(evidence)
            evidence_records.append(evidence)

            # Create citation
            cit = Citation(
                id=str(uuid.uuid4()),
                message_id=assistant_msg.id,
                chunk_id=claim_data.chunk_id,
                page_number=claim_data.page_number,
                quoted_text=claim_data.quote,
                citation_order=idx
            )
            db.add(cit)
            citation_records.append(cit)

        db.commit()

        # 7. Execute Claim-Level Citation Verification
        from app.services.verification_service import VerificationService
        verification_service = VerificationService()
        grounding_score = verification_service.verify_claims_and_citations(
            db=db,
            grounded_resp=grounded_resp,
            created_claims=claim_records,
            created_evidence=evidence_records,
            created_citations=citation_records
        )

        if grounding_score < 0.5 and len(grounded_resp.claims) > 0:
            assistant_msg.content += (
                "\n\n> [!WARNING]\n"
                "> **Grounding Warning:** Certain claims in this answer could not be verified "
                "against the cited document text."
            )
            db.commit()

        db.refresh(assistant_msg)

        # Format citation responses with document titles
        for cit in citation_records:
            doc_title = None
            if cit.chunk and cit.chunk.version and cit.chunk.version.document:
                doc_title = cit.chunk.version.document.title

            citation_responses.append(
                CitationResponse(
                    id=cit.id,
                    chunk_id=cit.chunk_id,
                    page_number=cit.page_number,
                    section_label=cit.section_label,
                    quoted_text=cit.quoted_text,
                    citation_order=cit.citation_order,
                    document_title=doc_title
                )
            )

        claim_responses = [
            ClaimResponse(
                id=cl.id,
                claim_text=cl.claim_text,
                claim_type=cl.claim_type,
                support_status=cl.support_status
            )
            for cl in assistant_msg.claims
        ]

        # Calculate verification summary status
        if not grounded_resp.claims:
            verification_status = "insufficient_evidence"
        elif grounding_score >= 0.7:
            verification_status = "supported"
        elif grounding_score >= 0.4:
            verification_status = "partially_supported"
        else:
            verification_status = "unverified"

        proc_details = ProcessingDetails(
            retrieval_method="hybrid (dense + keyword fused)",
            candidate_chunks=len(hits),
            context_chunks=len(hits),
            reranking_used=True,
            verification_performed=True,
            verification_status=verification_status,
            latency_ms=latency_ms
        )

        return MessageResponse(
            id=assistant_msg.id,
            conversation_id=conv.id,
            role="assistant",
            content=assistant_msg.content,
            model_name=assistant_msg.model_name,
            citations=citation_responses,
            claims=claim_responses,
            processing_details=proc_details,
            created_at=assistant_msg.created_at
        )

    def get_message_citations(self, db: Session, user: User, message_id: str) -> List[CitationResponse]:
        """Fetch evidentiary citations for a specific message ensuring tenant authorization."""
        message = (
            db.query(Message)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .filter(Message.id == message_id, Conversation.user_id == user.id)
            .first()
        )
        if not message:
            raise LegalAIException(
                message="Message not found or unauthorized.",
                code="MESSAGE_NOT_FOUND",
                status_code=404
            )
        citations = db.query(Citation).filter(Citation.message_id == message_id).order_by(Citation.citation_order).all()
        citation_responses = []
        for cit in citations:
            doc_title = None
            if cit.chunk and cit.chunk.version and cit.chunk.version.document:
                doc_title = cit.chunk.version.document.title
            citation_responses.append(
                CitationResponse(
                    id=cit.id,
                    chunk_id=cit.chunk_id,
                    page_number=cit.page_number,
                    section_label=cit.section_label,
                    quoted_text=cit.quoted_text,
                    citation_order=cit.citation_order,
                    document_title=doc_title
                )
            )
        return citation_responses
