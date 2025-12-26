"""
API测试
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()


def test_health_check():
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_intent_recognition():
    """测试意图识别API"""
    response = client.post(
        "/api/v1/nlu/intent",
        json={"text": "打开车窗"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data

