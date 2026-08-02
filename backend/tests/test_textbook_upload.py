import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from smartkcet.db.base import Base
from smartkcet.db.models import IndexedFile
from smartkcet.admin.upload import _record_indexed_file as _admin_record
from smartkcet.institution.content import _record_indexed_file as _inst_record

SQLALCHEMY_DATABASE_URL = "sqlite://"

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)

def test_admin_record_indexed_file_default(session):
    record = _admin_record(
        db=session,
        subject="Physics",
        filename="pyq_2025.pdf",
        file_hash="abc123hash",
        file_size=1024,
        chunk_count=5
    )
    assert record.subject == "Physics"
    assert record.filename == "pyq_2025.pdf"
    assert record.file_type == "question_paper"  # default
    assert record.file_hash == "abc123hash"
    assert record.file_size == 1024
    assert record.chunk_count == 5
    assert record.institution_id is None

def test_admin_record_indexed_file_textbook(session):
    record = _admin_record(
        db=session,
        subject="Chemistry",
        filename="ncert_chem_12.pdf",
        file_hash="chem123hash",
        file_size=2048,
        chunk_count=25,
        file_type="textbook"
    )
    assert record.subject == "Chemistry"
    assert record.filename == "ncert_chem_12.pdf"
    assert record.file_type == "textbook"
    assert record.file_hash == "chem123hash"
    assert record.file_size == 2048
    assert record.chunk_count == 25
    assert record.institution_id is None

def test_institution_record_indexed_file_textbook(session):
    inst_id = uuid.uuid4()
    record = _inst_record(
        db=session,
        subject="Biology",
        filename="campbell_bio.pdf",
        file_hash="bio456hash",
        file_size=4096,
        chunk_count=50,
        institution_id=inst_id,
        file_type="textbook"
    )
    assert record.subject == "Biology"
    assert record.filename == "campbell_bio.pdf"
    assert record.file_type == "textbook"
    assert record.file_hash == "bio456hash"
    assert record.file_size == 4096
    assert record.chunk_count == 50
    assert record.institution_id == inst_id
