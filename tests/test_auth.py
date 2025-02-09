# Author: SANJAY KR
import pytest
from app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        'TESTING': True
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_login_success(client):
    """Test successful login"""
    response = client.post('/api/v1/auth/token', data={
        'username': 'admin',
        'password': 'admin'
    })
    assert response.status_code == 200
    data = response.json
    assert 'access_token' in data
    assert data['token_type'] == 'bearer'

def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post('/api/v1/auth/token', data={
        'username': 'wrong',
        'password': 'wrong'
    })
    assert response.status_code == 401

def test_login_missing_credentials(client):
    """Test login with missing credentials"""
    response = client.post('/api/v1/auth/token', data={})
    assert response.status_code == 400
