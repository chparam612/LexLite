import os
import sys
import uuid
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure backend is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.db.session import SessionLocal
from app.models import (
    User,
    Document,
    DocumentVersion,
    DocumentPage,
    LegalSection,
    DocumentChunk,
    EmbeddingModel,
    Embedding,
    Conversation,
    ConversationDocument,
    Message
)


def seed_database():
    session = SessionLocal()
    try:
        print("🌱 Seeding database with initial legal domain data...")

        # 1. Embedding Model
        model = session.query(EmbeddingModel).filter_by(model_name="models/text-embedding-004").first()
        if not model:
            model = EmbeddingModel(
                id=str(uuid.uuid4()),
                provider="google",
                model_name="models/text-embedding-004",
                dimensions=768,
                version="004",
                is_active=True
            )
            session.add(model)
            session.flush()
            print(f"Created EmbeddingModel: {model.model_name}")

        # 2. Test User
        user = session.query(User).filter_by(email="attorney@legalai.example.com").first()
        if not user:
            user = User(
                id=str(uuid.uuid4()),
                firebase_uid="firebase_test_user_001",
                email="attorney@legalai.example.com",
                display_name="Sarah Jenkins, Esq."
            )
            session.add(user)
            session.flush()
            print(f"Created Test User: {user.email}")

        # 3. Sample Legal Document
        doc = session.query(Document).filter_by(title="Master Services Agreement (Demo)").first()
        if not doc:
            doc = Document(
                id=str(uuid.uuid4()),
                owner_id=user.id,
                title="Master Services Agreement (Demo)",
                document_type="contract",
                jurisdiction="State of New York",
                language="en",
                status="completed",
                page_count=3,
                file_size=1024 * 150,
                storage_key="seed/sample_msa.pdf",
                checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            )
            session.add(doc)
            session.flush()

            # Version
            version = DocumentVersion(
                id=str(uuid.uuid4()),
                document_id=doc.id,
                version_number=1,
                storage_key="seed/sample_msa.pdf",
                extraction_status="completed"
            )
            session.add(version)
            session.flush()

            # Pages
            page1 = DocumentPage(
                id=str(uuid.uuid4()),
                version_id=version.id,
                page_number=1,
                extracted_text="MASTER SERVICES AGREEMENT\nSection 1. Definitions...\nSection 2. Scope of Services...",
                ocr_used=False
            )
            page2 = DocumentPage(
                id=str(uuid.uuid4()),
                version_id=version.id,
                page_number=2,
                extracted_text="Section 7. Term and Termination.\n7.1 Termination for Convenience: Either party may terminate with 30 days written notice.",
                ocr_used=False
            )
            session.add_all([page1, page2])
            session.flush()

            # Section
            sec7 = LegalSection(
                id=str(uuid.uuid4()),
                version_id=version.id,
                section_number="7",
                heading="Term and Termination",
                section_type="section",
                page_start=2,
                page_end=2,
                full_text="Section 7. Term and Termination. Either party may terminate this Agreement for convenience upon giving at least thirty (30) days prior written notice to the other party."
            )
            session.add(sec7)
            session.flush()

            # Chunk
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                version_id=version.id,
                section_id=sec7.id,
                page_start=2,
                page_end=2,
                chunk_index=0,
                heading_path="Master Services Agreement > Section 7 (Term and Termination)",
                content="Either party may terminate this Agreement for convenience upon giving at least thirty (30) days prior written notice to the other party.",
                contextual_content="Document: Master Services Agreement | Jurisdiction: State of New York | Section 7: Term and Termination\n\nContent:\nEither party may terminate this Agreement for convenience upon giving at least thirty (30) days prior written notice to the other party.",
                token_count=32,
                checksum="abc123seedchecksum"
            )
            session.add(chunk)
            session.flush()

            # Embedding
            dummy_vec = [0.01 * (i % 50) for i in range(768)]
            emb = Embedding(
                id=str(uuid.uuid4()),
                chunk_id=chunk.id,
                model_id=model.id,
                embedding=dummy_vec
            )
            session.add(emb)

            # Sample conversation
            convo = Conversation(
                id=str(uuid.uuid4()),
                user_id=user.id,
                title="Termination Notice Query"
            )
            session.add(convo)
            session.flush()

            convo_doc = ConversationDocument(
                conversation_id=convo.id,
                document_id=doc.id
            )
            session.add(convo_doc)

            msg1 = Message(
                id=str(uuid.uuid4()),
                conversation_id=convo.id,
                role="user",
                content="What is the notice period required for termination for convenience?"
            )
            msg2 = Message(
                id=str(uuid.uuid4()),
                conversation_id=convo.id,
                role="assistant",
                content="Either party may terminate the Agreement for convenience upon giving at least thirty (30) days prior written notice (Section 7, Page 2)."
            )
            session.add_all([msg1, msg2])
            print("Created Sample Document, Chunks, Embeddings, and Conversation.")

        session.commit()
        print("✅ Database seeding successfully completed.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
