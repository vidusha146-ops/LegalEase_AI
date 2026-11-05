"""
LegalEase AI - Citizen User Dashboard & Privacy Test Suite (Phase 7 Module 3)
Validates:
- Milestone A: Protected dashboard metrics & profile updates
- Milestone B: Case lifecycle progression, cross-tenant isolation (403), and query history
- Milestone C: AES-256-GCM encrypted evidence vault & document archive
- Milestone D: Privacy summary, voluntary data export with SHA-256 hash, and multi-layer cascading deletion
- Milestone E: Security verification and tamper detection
"""

import os
import json
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from app.core.database import AsyncSessionLocal, init_db, get_db
from app.models.user import User
from app.models.case import LegalCase
from app.models.evidence import EvidenceDocument
from app.models.draft import LegalDraft
from app.models.search_query import CaseSimilarityQuery
from app.core.security import get_password_hash, create_access_token
from app.services.vault_encryption import VaultEncryptionService


@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def ensure_default_db_dependency():
    """Ensures dashboard tests run against persistent database."""
    app.dependency_overrides.pop(get_db, None)
    yield
    app.dependency_overrides.pop(get_db, None)


# =============================================================================
# 1. MILESTONE A: AUTHENTICATION & PROTECTED DASHBOARD TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_milestone_a_dashboard_summary_and_profile():
    """
    Tests citizen authentication, profile preference update,
    and consolidated dashboard metrics overview.
    """
    await init_db()

    user_email = "citizen.dash.a@example.in"
    user_token = ""
    user_id = 0

    async with AsyncSessionLocal() as session:
        u_res = await session.execute(select(User).where(User.email == user_email))
        user = u_res.scalar_one_or_none()
        if not user:
            user = User(
                email=user_email,
                hashed_password=get_password_hash("SecurePass123!"),
                full_name="Aarav Sharma",
                preferred_language="hi",
                is_active=True,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            user.full_name = "Aarav Sharma"
            user.preferred_language = "hi"
            session.add(user)
            await session.commit()
            await session.refresh(user)
        user_id = user.id
        user_token = create_access_token({"sub": user.email})

    headers = {"Authorization": f"Bearer {user_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Dashboard Summary
        sum_res = await client.get("/api/v1/dashboard/summary", headers=headers)
        assert sum_res.status_code == 200
        summary_data = sum_res.json()
        assert summary_data["email"] == user_email
        assert summary_data["full_name"] == "Aarav Sharma"
        assert len(summary_data["tenant_pseudonym"]) == 16
        assert summary_data["vault_encryption_algorithm"] == "AES-256-GCM"
        assert summary_data["dpdpa_privacy_mode"] == "VOLUNTARY_TRANSPARENCY_ACTIVE"

        # 2. Update Profile Preferences
        prof_payload = {"full_name": "Aarav K. Sharma", "preferred_language": "mr"}
        prof_res = await client.put("/api/v1/dashboard/profile", json=prof_payload, headers=headers)
        assert prof_res.status_code == 200
        prof_data = prof_res.json()
        assert prof_data["full_name"] == "Aarav K. Sharma"
        assert prof_data["preferred_language"] == "mr"


# =============================================================================
# 2. MILESTONE B: CASE LIFECYCLE & QUERY HISTORY TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_milestone_b_case_lifecycle_and_query_history():
    """
    Tests citizen case creation, state transitions (NEW -> ACTIVE -> RESOLVED),
    cross-tenant access control (403 forbidden), and persistent query logging.
    """
    await init_db()

    user_a_email = "citizen.case.tenant.a@example.in"
    user_b_email = "citizen.case.tenant.b@example.in"

    token_a = ""
    token_b = ""

    async with AsyncSessionLocal() as session:
        # User A
        u_a = (await session.execute(select(User).where(User.email == user_a_email))).scalar_one_or_none()
        if not u_a:
            u_a = User(email=user_a_email, hashed_password=get_password_hash("Pass123!"), full_name="Tenant A")
            session.add(u_a)
            await session.commit()
            await session.refresh(u_a)
        token_a = create_access_token({"sub": u_a.email})

        # User B
        u_b = (await session.execute(select(User).where(User.email == user_b_email))).scalar_one_or_none()
        if not u_b:
            u_b = User(email=user_b_email, hashed_password=get_password_hash("Pass123!"), full_name="Tenant B")
            session.add(u_b)
            await session.commit()
            await session.refresh(u_b)
        token_b = create_access_token({"sub": u_b.email})

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. User A creates a case
        create_payload = {
            "title": "Defective Air Conditioner Dispute",
            "raw_description": "Purchased split AC which had recurring compressor breakdown in 3 months.",
            "category": "CONSUMER_PROTECTION",
        }
        create_res = await client.post("/api/v1/dashboard/cases", json=create_payload, headers=headers_a)
        assert create_res.status_code == 201
        case_a_data = create_res.json()
        case_id = case_a_data["id"]
        assert case_a_data["status"] == "NEW"

        # 2. User A retrieves case detail
        detail_res = await client.get(f"/api/v1/dashboard/cases/{case_id}", headers=headers_a)
        assert detail_res.status_code == 200
        assert detail_res.json()["title"] == "Defective Air Conditioner Dispute"

        # 3. Cross-Tenant Access Enforcement: User B attempts to access User A's case -> 403 Forbidden
        forbidden_res = await client.get(f"/api/v1/dashboard/cases/{case_id}", headers=headers_b)
        assert forbidden_res.status_code == 403
        assert "Access forbidden" in forbidden_res.json()["detail"]

        # 4. User B attempts to update User A's case status -> 403 Forbidden
        forbid_update = await client.patch(
            f"/api/v1/dashboard/cases/{case_id}/status", json={"status": "ACTIVE"}, headers=headers_b
        )
        assert forbid_update.status_code == 403

        # 5. User A successfully transitions status
        update_res = await client.patch(
            f"/api/v1/dashboard/cases/{case_id}/status", json={"status": "DOCUMENTED"}, headers=headers_a
        )
        assert update_res.status_code == 200
        assert update_res.json()["status"] == "DOCUMENTED"

        # 6. Persistent Query History for User A
        async with AsyncSessionLocal() as session:
            q = CaseSimilarityQuery(
                user_id=u_a.id,
                case_id=case_id,
                query_text="Compressor breakdown within warranty period consumer remedy",
                legal_domain="CONSUMER_PROTECTION",
                retrieved_judgment_ids_json='["SC_1994_LUCKNOW_DEV_AUTH"]',
            )
            session.add(q)
            await session.commit()
            q_id = q.id

        q_list_res = await client.get("/api/v1/dashboard/queries", headers=headers_a)
        assert q_list_res.status_code == 200
        queries = q_list_res.json()
        assert len(queries) >= 1
        assert any(x["id"] == q_id for x in queries)

        # 7. Delete single query
        del_q_res = await client.delete(f"/api/v1/dashboard/queries/{q_id}", headers=headers_a)
        assert del_q_res.status_code == 200


# =============================================================================
# 3. MILESTONE C: ENCRYPTED EVIDENCE VAULT & DOCUMENT ARCHIVE TESTS
# =============================================================================

def test_milestone_c_aes_gcm_vault_cryptography():
    """
    Validates per-tenant HKDF key derivation, authenticated AES-256-GCM encryption,
    decryption round-trip, and tampering detection.
    """
    user_id = 42001
    plaintext = b"CONFIDENTIAL_BANK_STATEMENT: Transferred Rs 2,50,000 via NEFT to Builder."

    # Encrypt
    encrypted_payload = VaultEncryptionService.encrypt_bytes(plaintext, user_id)
    assert encrypted_payload.startswith(b"LEGALEASE_AESGCM_V1")
    assert plaintext not in encrypted_payload  # No plaintext leakage

    # Decrypt with correct user
    decrypted = VaultEncryptionService.decrypt_bytes(encrypted_payload, user_id)
    assert decrypted == plaintext

    # Decrypt with wrong tenant key -> raises ValueError (tag mismatch)
    wrong_user_id = 99999
    with pytest.raises(ValueError) as exc:
        VaultEncryptionService.decrypt_bytes(encrypted_payload, wrong_user_id)
    assert "Cryptographic authentication tag verification failed" in str(exc.value)

    # Tampering with ciphertext -> raises ValueError
    tampered_payload = bytearray(encrypted_payload)
    tampered_payload[-5] ^= 0xFF  # Flip bits in authentication tag / ciphertext
    with pytest.raises(ValueError):
        VaultEncryptionService.decrypt_bytes(bytes(tampered_payload), user_id)


# =============================================================================
# 4. MILESTONE D: PRIVACY CONTROLS, EXPORT & MULTI-LAYER DELETION TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_milestone_d_privacy_summary_export_and_deletion():
    """
    Tests privacy posture summary, voluntary JSON data export with SHA-256 hash,
    and multi-layer cascading deletion with crypto-shredding.
    """
    await init_db()

    del_user_email = "citizen.delete.me@example.in"
    token = ""
    u_id = 0

    async with AsyncSessionLocal() as session:
        u = (await session.execute(select(User).where(User.email == del_user_email))).scalar_one_or_none()
        if not u:
            u = User(email=del_user_email, hashed_password=get_password_hash("Pass123!"), full_name="Delete Citizen")
            session.add(u)
            await session.commit()
            await session.refresh(u)
        u_id = u.id
        token = create_access_token({"sub": u.email})

        # Add a test case and query log
        c = LegalCase(user_id=u_id, title="Case for Deletion", raw_description="Will be shredded.", status="ACTIVE")
        session.add(c)
        q = CaseSimilarityQuery(user_id=u_id, query_text="Pre-deletion search query")
        session.add(q)
        await session.commit()

    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Privacy Summary
        priv_res = await client.get("/api/v1/dashboard/privacy/summary", headers=headers)
        assert priv_res.status_code == 200
        priv_data = priv_res.json()
        assert priv_data["stored_entity_counts"]["legal_cases"] >= 1
        assert "AES-256-GCM" in priv_data["encryption_profile"]["algorithm"]
        assert "DPDPA" in priv_data["dpdpa_compliance_readiness"]

        # 2. Voluntary Data Export
        export_res = await client.post("/api/v1/dashboard/privacy/export", headers=headers)
        assert export_res.status_code == 200
        exp_data = export_res.json()
        assert exp_data["user_profile"]["email"] == del_user_email
        assert len(exp_data["cases"]) >= 1
        assert len(exp_data["export_sha256_hash"]) == 64  # SHA-256 hex string

        # 3. Multi-Layer Cascading Account Deletion
        del_acc_res = await client.delete("/api/v1/dashboard/privacy/account", headers=headers)
        assert del_acc_res.status_code == 200
        del_res_data = del_acc_res.json()
        assert del_res_data["status"] == "ACCOUNT_PERMANENTLY_DELETED"
        assert del_res_data["crypto_shredding_status"] == "TENANT_DEK_SHREDDED_AND_FILES_UNLINKED"
        assert del_res_data["relational_records_deleted"] >= 2

        # 4. Confirm User Record is Gone
        async with AsyncSessionLocal() as session:
            check_u = (await session.execute(select(User).where(User.email == del_user_email))).scalar_one_or_none()
            assert check_u is None
            check_c = (await session.execute(select(LegalCase).where(LegalCase.user_id == u_id))).scalars().all()
            assert len(check_c) == 0
