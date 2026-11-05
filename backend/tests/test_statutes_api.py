import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_statutes_search_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/statutes/search?query=dishonest+taking+property&top_k=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_retrieved"] > 0
        assert len(data["results"]) > 0


@pytest.mark.asyncio
async def test_crosswalk_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Theft Definition IPC 378
        resp_def = await client.get("/api/v1/statutes/crosswalk/ipc/378")
        assert resp_def.status_code == 200
        data_def = resp_def.json()
        assert data_def["matched_role"] == "DEFINITION"
        assert "303(1)" in data_def["bns_definition"]

        # 2. Theft Punishment IPC 379
        resp_pun = await client.get("/api/v1/statutes/crosswalk/ipc/379")
        assert resp_pun.status_code == 200
        data_pun = resp_pun.json()
        assert data_pun["matched_role"] == "PUNISHMENT"
        assert "303(2)" in data_pun["bns_punishment"]

        # 3. Non-existent Section
        resp_404 = await client.get("/api/v1/statutes/crosswalk/ipc/9999")
        assert resp_404.status_code == 404

        # 4. Temporal Applicability
        temp_resp = await client.post(
            "/api/v1/statutes/crosswalk/temporal-applicability",
            json={"date_of_incident": "2024-04-12", "is_continuing": False},
        )
        assert temp_resp.status_code == 200
        temp_data = temp_resp.json()
        assert temp_data["status"] == "HISTORICAL_IPC"
        assert "Section 358" in temp_data["savings_clause"]


@pytest.mark.asyncio
async def test_citation_verification_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "text": "Accused committed fraud under Section 420 IPC and Section 318(4) of Bharatiya Nyaya Sanhita, but falsely cited Section 9999 BNS."
        }
        resp = await client.post("/api/v1/statutes/verify-citations", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_citations"] == 3
        assert data["valid_count"] == 2
        assert data["invalid_count"] == 1
