# WhatsApp Bot for Family & Samaj Data Collection

A Flask-based WhatsApp bot application that collects, stores, and manages family and Samaj-wise information through an interactive chat interface.

## Features

- WhatsApp integration using Twilio API with comprehensive error handling
- Interactive data collection through WhatsApp chat with input validation
- PostgreSQL database with SQLAlchemy ORM for robust data management
- Flask backend with JWT authentication and admin dashboard
- Docker containerization with multi-container orchestration
- Media message rejection and stateful conversation tracking
- Comprehensive logging and error monitoring
- CI/CD pipeline with automated testing

## Additional Data Fields

Beyond the core columns, we've added 20 additional fields to capture comprehensive family information:

1. Education - Educational qualifications
2. Occupation - Current profession
3. Marital Status - Current marital status
4. Address - Current residential address
5. Email - Contact email address
6. Birth Date - Date of birth
7. Anniversary Date - Marriage anniversary date
8. Native Place - Place of origin
9. Current City - Current city of residence
10. Languages Known - Languages spoken/written
11. Skills - Professional/personal skills
12. Hobbies - Personal interests
13. Emergency Contact - Emergency contact information
14. Relationship Status - Family relationship status
15. Family Role - Role in the family
16. Medical Conditions - Important health information
17. Dietary Preferences - Food preferences/restrictions
18. Social Media Handles - Social media profiles
19. Profession Category - Industry/sector of work
20. Volunteer Interests - Areas of community service interest

## Setup Instructions

1. Clone the repository
2. Create a .env file with required credentials
3. Run with Docker:
   ```bash
   docker-compose up --build
   ```

## Development Setup

### Local Development
1. Install dependencies:
   ```bash
   poetry install
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. Initialize database:
   ```bash
   python scripts/init_db.py
   python scripts/generate_sample_data.py
   ```

4. Run the application:
   ```bash
   flask run --host=0.0.0.0 --port=8000
   ```

### Docker Development
1. Build and start services:
   ```bash
   docker-compose up --build
   ```

2. Monitor logs:
   ```bash
   docker-compose logs -f
   ```

## API Documentation

### Authentication
```bash
# Get JWT token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Use token for protected endpoints
curl -X GET http://localhost:8000/admin/members \
  -H "Authorization: Bearer your_jwt_token"
```

### Key Endpoints
- POST /webhook: WhatsApp message webhook
- POST /auth/login: Admin authentication
- GET /admin/members: List all members
- GET /admin/samaj: List all Samaj records

## Environment Variables

Required environment variables:
```
DATABASE_URL          # PostgreSQL connection string
TWILIO_ACCOUNT_SID   # Your Twilio Account SID
TWILIO_AUTH_TOKEN    # Your Twilio Auth Token
JWT_SECRET_KEY       # Secret key for JWT encryption
JWT_ALGORITHM        # JWT encryption algorithm (e.g., HS256)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES  # Token expiration time
ADMIN_USERNAME       # Admin panel username
ADMIN_PASSWORD       # Admin panel password
TWILIO_PHONE_NUMBER  # Your Twilio WhatsApp number
```

Note: Never commit actual credentials. Use environment variables to manage sensitive information securely.

## Project Structure

```
├── app/
│   ├── controllers/      # Business logic for user interactions
│   │   ├── admin_controller.py    # Admin panel operations
│   │   ├── auth_controller.py     # Authentication handling
│   │   └── whatsapp_controller.py # Message processing
│   ├── models/          # Database schema definitions
│   │   ├── base.py     # Base model configuration
│   │   └── family.py   # Samaj and Member models
│   ├── services/        # Business logic services
│   │   └── whatsapp_service.py # WhatsApp message handling
│   ├── routes/          # API endpoint definitions
│   │   ├── admin.py    # Admin panel routes
│   │   ├── auth.py     # Authentication routes
│   │   └── whatsapp.py # WhatsApp webhook
│   └── utils/           # Helper functions
├── tests/               # Unit and integration tests
│   ├── test_admin.py   # Admin functionality tests
│   ├── test_auth.py    # Authentication tests
│   └── test_whatsapp.py # WhatsApp integration tests
├── scripts/             # Utility scripts
│   ├── init_db.py      # Database initialization
│   ├── check_db.py     # Database verification
│   └── generate_sample_data.py # Sample data creation
├── config/             # Configuration files
│   └── settings.py    # Application settings
├── docker-compose.yml  # Multi-container Docker setup
├── Dockerfile         # Container build instructions
├── pyproject.toml    # Poetry dependencies
├── README.md         # Project documentation
├── swagger.yaml      # API documentation
└── .github/          # CI/CD configuration
    └── workflows/    # GitHub Actions workflows
```

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

1. Environment Setup:
   - Python 3.12 installation
   - Poetry package manager
   - PostgreSQL service container

2. Testing Pipeline:
   - Dependencies installation
   - Database initialization
   - Unit tests execution
   - Integration tests
   - Docker build verification

3. Deployment Steps:
   - Environment validation
   - Container building
   - Service deployment

### GitHub Actions Configuration

```yaml
name: CI/CD Pipeline
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: whatsapp_bot_test
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install Poetry
        run: pip install poetry
      - name: Install dependencies
        run: poetry install
      - name: Run tests
        run: poetry run pytest
```

## Troubleshooting Guide

### Common Issues and Solutions

1. Database Connection Issues:
   ```bash
   # Check database status
   python scripts/check_db.py
   
   # Common solutions:
   - Verify PostgreSQL service: docker-compose ps
   - Check credentials in .env
   - Ensure database exists: psql -U postgres -c '\l'
   ```

2. WhatsApp Integration:
   ```bash
   # Verify Twilio configuration
   python scripts/check_config.py
   
   # Common solutions:
   - Update Twilio credentials
   - Check webhook URL format
   - Verify SSL certificate
   ```

3. Docker Issues:
   ```bash
   # Container management
   docker-compose down
   docker system prune
   docker-compose up --build
   
   # View logs
   docker-compose logs -f web
   docker-compose logs -f db
   ```

4. Authentication Problems:
   ```bash
   # Test authentication
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin"}'
   
   # Common solutions:
   - Check JWT configuration
   - Verify admin credentials
   - Clear browser cache
   ```

### Error Messages and Solutions

1. "Database connection failed":
   - Check DATABASE_URL format
   - Verify PostgreSQL container is running
   - Ensure network connectivity

2. "Invalid Twilio credentials":
   - Verify TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN
   - Check for whitespace in credentials
   - Validate webhook URL format

3. "JWT token verification failed":
   - Check JWT_SECRET_KEY configuration
   - Verify token expiration time
   - Ensure correct token format

4. "Media message rejected":
   - This is expected behavior
   - Only text messages are supported
   - Remove media attachments
