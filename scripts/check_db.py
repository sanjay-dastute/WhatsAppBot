# Author: SANJAY KR
from app import create_app, db
from app.models.family import Samaj, Member

app = create_app()
with app.app_context():
    try:
        db.create_all()
        samaj_count = db.session.query(Samaj).count()
        member_count = db.session.query(Member).count()
        print(f'Total Samaj records: {samaj_count}')
        print(f'Total Member records: {member_count}')
    except Exception as e:
        print(f'Error checking database: {str(e)}')
