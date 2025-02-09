# Author: SANJAY KR
import pytest
from app import create_app
from app.models.family import Samaj, Member

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'postgresql://postgres:postgres@localhost:5432/whatsapp_bot_test'
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_webhook_start_message(client):
    """Test the webhook endpoint with a start message"""
    response = client.post('/api/v1/webhook', data={
        'From': 'whatsapp:+1234567890',
        'Body': 'start'
    })
    assert response.status_code == 200
    assert response.json['success'] == True

def test_webhook_invalid_request(client):
    """Test the webhook endpoint with missing data"""
    response = client.post('/api/v1/webhook', data={})
    assert response.status_code == 500

def test_webhook_data_collection(client):
    """Test the webhook endpoint for data collection flow"""
    phone = 'whatsapp:+1234567890'
    test_responses = [
        ('start', 200),
        ('Test Samaj', 200),
        ('John Doe', 200),
        ('Male', 200),
        ('30', 200),
        ('O+', 200),
        ('+1234567890', 200),
        ('+0987654321', 200)
    ]
    
    for message, expected_status in test_responses:
        response = client.post('/api/v1/webhook', data={
            'From': phone,
            'Body': message
        })
        assert response.status_code == expected_status
