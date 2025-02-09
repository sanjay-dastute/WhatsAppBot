# Author: SANJAY KR
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')
    CORS(app)
    
    # Load all configurations first
    app.config.update(
        DEBUG=True,
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/whatsapp_bot'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'development-secret-key-do-not-use-in-production'),
        JWT_ALGORITHM=os.environ.get('JWT_ALGORITHM', 'HS256'),
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30')),
        ADMIN_USERNAME=os.environ.get('ADMIN_USERNAME', 'admin'),
        ADMIN_PASSWORD=os.environ.get('ADMIN_PASSWORD', 'admin')
    )
    
    # Configure logging
    import logging
    import sys
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)
    
    app.logger.info("Starting Flask application")
    
    # Log environment variables
    app.logger.info("Environment variables:")
    for key, value in os.environ.items():
        if not any(sensitive in key.lower() for sensitive in ['password', 'secret', 'token']):
            app.logger.info(f"{key}: {value}")
            
    # Set Flask secret key
    app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'development-secret-key-do-not-use-in-production')
    app.logger.info("Flask configuration loaded")
    
    # Load configuration
    # JWT Configuration
    app.config.update(
        JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'development-secret-key-do-not-use-in-production'),
        JWT_ALGORITHM=os.environ.get('JWT_ALGORITHM', 'HS256'),
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30')),
        ADMIN_USERNAME=os.environ.get('ADMIN_USERNAME', 'admin'),
        ADMIN_PASSWORD=os.environ.get('ADMIN_PASSWORD', 'admin')
    )
    
    # Log configuration status
    app.logger.info(f"JWT_ALGORITHM: {app.config['JWT_ALGORITHM']}")
    app.logger.info(f"JWT_ACCESS_TOKEN_EXPIRE_MINUTES: {app.config['JWT_ACCESS_TOKEN_EXPIRE_MINUTES']}")
    app.logger.info(f"JWT_SECRET_KEY is set: {bool(app.config['JWT_SECRET_KEY'])}")
    app.logger.info(f"JWT_SECRET_KEY configured: {bool(app.config.get('JWT_SECRET_KEY'))}")
    app.logger.info(f"JWT_ALGORITHM configured: {app.config.get('JWT_ALGORITHM')}")
    app.logger.info("Flask configuration loaded successfully")
    
    # Verify configuration loaded correctly
    app.logger.info("Verifying configuration...")
    app.logger.info(f"ADMIN_USERNAME: {app.config.get('ADMIN_USERNAME')}")
    app.logger.info(f"JWT_SECRET_KEY: {bool(app.config.get('JWT_SECRET_KEY'))}")
    app.logger.info(f"JWT_ALGORITHM: {app.config.get('JWT_ALGORITHM')}")
    
    # Ensure critical config values are set
    assert app.config.get('ADMIN_USERNAME'), "ADMIN_USERNAME must be configured"
    assert app.config.get('ADMIN_PASSWORD'), "ADMIN_PASSWORD must be configured"
    assert app.config.get('JWT_SECRET_KEY'), "JWT_SECRET_KEY must be configured"
    
    # Log configuration values for debugging (without sensitive data)
    app.logger.info("Configuration loaded:")
    app.logger.info(f"JWT_ALGORITHM: {app.config['JWT_ALGORITHM']}")
    app.logger.info(f"JWT_ACCESS_TOKEN_EXPIRE_MINUTES: {app.config['JWT_ACCESS_TOKEN_EXPIRE_MINUTES']}")
    app.logger.info(f"JWT_SECRET_KEY is set: {bool(app.config.get('JWT_SECRET_KEY'))}")
    
    # Log configuration for debugging
    app.logger.info(f"JWT_SECRET_KEY configured: {bool(app.config.get('JWT_SECRET_KEY'))}")
    app.logger.info(f"JWT_ALGORITHM configured: {app.config.get('JWT_ALGORITHM')}")
    
    # Ensure critical config values are set
    assert "JWT_SECRET_KEY" in app.config, "JWT_SECRET_KEY must be configured"
    assert "JWT_ACCESS_TOKEN_EXPIRE_MINUTES" in app.config, "JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be configured"
    
    app.logger.info("Flask configuration loaded successfully")
    
    db.init_app(app)
    
    with app.app_context():
        try:
            app.logger.info("Initializing database connection...")
            app.logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            app.logger.info("Checking database tables...")
            from .models.family import Samaj, Member
            
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            app.logger.info(f"Existing tables: {existing_tables}")
            
            if not existing_tables:
                app.logger.info("Creating database tables...")
                db.create_all()
                app.logger.info("Database tables created successfully")
                
                # Check if there's any data
                samaj_count = db.session.query(Samaj).count()
                if samaj_count == 0:
                    app.logger.info("Generating sample data...")
                    try:
                        from app.utils.generate_sample_data import generate_sample_data
                        generate_sample_data(db.session, 50)
                        app.logger.info("Sample data generated successfully")
                    except Exception as e:
                        app.logger.error(f"Error during sample data generation: {str(e)}")
                        db.session.rollback()
                        raise
                    app.logger.info("Sample data generation completed")
                else:
                    app.logger.info(f"Using existing data: {samaj_count} samaj records found")
            else:
                app.logger.info(f"Using existing tables: {existing_tables}")
            
            if db.session.query(Samaj).first() is None:
                app.logger.info("Generating sample data...")
                try:
                    from app.utils.generate_sample_data import generate_sample_data
                    generate_sample_data(db.session, 50)
                    app.logger.info("Sample data generated successfully")
                except Exception as e:
                    app.logger.error(f"Error during sample data generation: {str(e)}")
                    db.session.rollback()
                    raise
                app.logger.info("Sample data generation completed")
        except Exception as e:
            app.logger.error(f"Error during database initialization: {str(e)}")
            raise
    
    # Initialize WhatsApp service before routes
    from .services.whatsapp_service import WhatsAppService, get_whatsapp_service
    
    # Initialize service in app context
    with app.app_context():
        get_whatsapp_service()
    
    from .routes.whatsapp import whatsapp_bp
    from .routes.admin import admin_bp
    from .routes.auth import auth_bp
    
    app.register_blueprint(whatsapp_bp, url_prefix="/api/v1/whatsapp")
    app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    
    # Register CLI commands
    from .cli import check_db
    app.cli.add_command(check_db)
    
    return app
