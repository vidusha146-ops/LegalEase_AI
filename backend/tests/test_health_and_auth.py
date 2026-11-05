import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.database import Base, get_db
from app.main import app

# Use an isolated test SQLite database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def setup_test_database():
    """Create all tables before each test and drop them after."""
    app.dependency_overrides[get_db] = override_get_db
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_root_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "LegalEase AI" in data["app"]
        assert data["status"] == "online"
        assert "Advocates Act, 1961" in data["disclaimer"]


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database_status"] == "connected"
        assert "1915" in data["helplines"]["NATIONAL_CONSUMER_HELPLINE"]
        assert "1930" in data["helplines"]["NATIONAL_CYBER_CRIME_REPORTING"]


@pytest.mark.asyncio
async def test_auth_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register a new citizen
        register_payload = {
            "email": "citizen.sharma@example.in",
            "password": "StrongPassword123!",
            "full_name": "Ramesh Sharma",
            "preferred_language": "hi",
        }
        reg_response = await client.post("/api/v1/auth/register", json=register_payload)
        assert reg_response.status_code == 201
        reg_data = reg_response.json()
        assert "access_token" in reg_data
        assert reg_data["user"]["email"] == "citizen.sharma@example.in"
        assert reg_data["user"]["full_name"] == "Ramesh Sharma"
        assert reg_data["user"]["preferred_language"] == "hi"

        token = reg_data["access_token"]

        # 2. Prevent duplicate email registration
        dup_response = await client.post("/api/v1/auth/register", json=register_payload)
        assert dup_response.status_code == 400
        assert "already exists" in dup_response.json()["detail"]

        # 3. Successful JSON Login
        login_payload = {
            "email": "citizen.sharma@example.in",
            "password": "StrongPassword123!",
        }
        login_response = await client.post("/api/v1/auth/login", json=login_payload)
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data

        # 4. Failed Login with Wrong Password
        wrong_pwd_response = await client.post("/api/v1/auth/login", json={
            "email": "citizen.sharma@example.in",
            "password": "WrongPassword123!",
        })
        assert wrong_pwd_response.status_code == 401

        # 5. Access Protected /me endpoint with valid token
        headers = {"Authorization": f"Bearer {token}"}
        me_response = await client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["email"] == "citizen.sharma@example.in"
        assert me_data["full_name"] == "Ramesh Sharma"

        # 6. Unauthorized access without token
        unauth_response = await client.get("/api/v1/auth/me")
        assert unauth_response.status_code == 401
