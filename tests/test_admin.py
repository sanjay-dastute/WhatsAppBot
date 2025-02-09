# Author: SANJAY KR
import pytest
from app import create_app, db
from app.models.family import Samaj, Member

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'postgresql://postgres:postgres@localhost:5432/whatsapp_bot_test'
    })
    
    with app.app_context():
        db.create_all()
        
        # Create test data
        samaj = Samaj(name='Test Samaj')
        db.session.add(samaj)
        db.session.commit()
        
        member = Member(
            samaj_id=samaj.id,
            name='John Doe',
            gender='Male',
            age=30,
            blood_group='O+',
            mobile_1='+1234567890'
        )
        db.session.add(member)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers():
    """Get authentication token"""
    return {'Authorization': 'Bearer test-token'}

def test_list_members(client, auth_headers):
    """Test listing all members"""
    response = client.get('/api/v1/admin/members', headers=auth_headers)
    assert response.status_code == 200
    data = response.json
    assert len(data) > 0
    assert data[0]['name'] == 'John Doe'

def test_list_samaj(client, auth_headers):
    """Test listing all samaj"""
    response = client.get('/api/v1/admin/samaj', headers=auth_headers)
    assert response.status_code == 200
    data = response.json
    assert len(data) > 0
    assert data[0]['name'] == 'Test Samaj'

def test_get_member(client, auth_headers):
    """Test getting a specific member"""
    response = client.get('/api/v1/admin/members/1', headers=auth_headers)
    assert response.status_code == 200
    data = response.json
    assert data['name'] == 'John Doe'

def test_export_csv(client, auth_headers):
    """Test exporting members as CSV"""
    response = client.get('/api/v1/admin/export/csv', headers=auth_headers)
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv'
