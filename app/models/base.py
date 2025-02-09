# Author: SANJAY KR
from flask import current_app
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import scoped_session, sessionmaker
from .. import db

def init_db():
    try:
        with current_app.app_context():
            current_app.logger.info("Starting database initialization...")
            current_app.logger.info(f"Database URI: {current_app.config['SQLALCHEMY_DATABASE_URI']}")
            
            # Import models to ensure they are registered with SQLAlchemy
            from ..models.family import Samaj, Member
            current_app.logger.info("Models imported")
            
            # Test database connection
            engine = db.get_engine()
            current_app.logger.info("Testing database connection...")
            conn = engine.connect()
            conn.close()
            current_app.logger.info("Database connection successful")
            
            # Drop all tables and recreate them
            current_app.logger.info("Dropping existing tables...")
            db.drop_all()
            current_app.logger.info("Creating database tables...")
            db.create_all()
            
            # Verify tables
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            current_app.logger.info(f"Created tables: {tables}")
            
            if not tables:
                raise Exception("No tables were created")
                
            current_app.logger.info("Database initialization completed successfully")
            return True
    except Exception as e:
        current_app.logger.error(f"Database initialization error: {str(e)}")
        raise

def get_db():
    try:
        if not hasattr(db, 'session'):
            engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
            db.session = scoped_session(sessionmaker(bind=engine))
            current_app.logger.info("Created new database session")
        return db.session
    except Exception as e:
        current_app.logger.error(f"Database session error: {str(e)}")
        raise
