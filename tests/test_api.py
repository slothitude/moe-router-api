"""Basic API tests."""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "MoE Router API"
    assert "endpoints" in data


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_list_models(client):
    """Test list models endpoint."""
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) > 0


def test_model_pool_status(client):
    """Test model pool status endpoint."""
    response = client.get("/api/v1/models/pool")
    assert response.status_code == 200
    data = response.json()
    assert "gpu_models" in data
    assert "ram_models" in data


def test_cache_stats(client):
    """Test cache statistics endpoint."""
    response = client.get("/api/v1/cache/stats")
    assert response.status_code == 200
    data = response.json()
    assert "size" in data
    assert "hits" in data
