# Author: SANJAY KR
import pytest
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(autouse=True)
def env_setup():
    """Setup environment variables for testing"""
    os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost:5432/whatsapp_bot_test'
    os.environ['JWT_SECRET_KEY'] = 'test-secret-key'
    os.environ['ADMIN_USERNAME'] = 'admin'
    os.environ['ADMIN_PASSWORD'] = 'admin'
