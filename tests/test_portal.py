import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from backend.models.approval_token import ApprovalToken

def test_approval_token_model_exists():
    assert hasattr(ApprovalToken, "__tablename__")
    assert ApprovalToken.__tablename__ == "approval_tokens"

def test_approval_token_has_required_fields():
    cols = {c.name for c in ApprovalToken.__table__.columns}
    assert "id" in cols
    assert "token" in cols
    assert "client_id" in cols
    assert "project_id" in cols
    assert "expires_at" in cols
    assert "created_by" in cols
    assert "active" in cols
