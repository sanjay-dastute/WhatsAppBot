# Author: SANJAY KR
from app import create_app, db
from app.models.family import Samaj, Member

def init_database():
    app = create_app()
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if not existing_tables:
                print("Creating all tables...")
                db.create_all()
                
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()
                print(f"Created tables: {tables}")
                
                if not tables:
                    raise Exception("No tables were created")
            else:
                print(f"Tables already exist: {existing_tables}")
                
            print("Database initialization completed successfully")
            return True
        except Exception as e:
            print(f"Database initialization error: {str(e)}")
            raise

if __name__ == "__main__":
    init_database()
