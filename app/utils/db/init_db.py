# Author: SANJAY KR
import json
import os
from app import create_app, db
from app.models.family import Samaj, Member

def init_db_with_sample_data():
    app = create_app()
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Load sample data
        with open(os.path.join(os.path.dirname(__file__), '../../../scripts/sample_data.json')) as f:
            data = json.load(f)
        
        # Create Samaj entries
        samaj_map = {}
        for record in data:
            if record['samaj'] not in samaj_map:
                samaj = Samaj(name=record['samaj'])
                db.session.add(samaj)
                db.session.flush()
                samaj_map[record['samaj']] = samaj.id
        
        # Create Member entries
        for record in data:
            member = Member(
                samaj_id=samaj_map[record['samaj']],
                name=record['name'],
                gender=record['gender'],
                age=record['age'],
                blood_group=record['blood_group'],
                mobile_1=record['mobile_1'],
                mobile_2=record['mobile_2'],
                education=record['education'],
                occupation=record['occupation'],
                marital_status=record['marital_status'],
                address=record['address'],
                email=record['email'],
                birth_date=record['birth_date'],
                anniversary_date=record['anniversary_date'],
                native_place=record['native_place'],
                current_city=record['current_city'],
                languages_known=record['languages_known'],
                skills=record['skills'],
                hobbies=record['hobbies'],
                emergency_contact=record['emergency_contact'],
                relationship_status=record['relationship_status'],
                family_role=record['family_role'],
                medical_conditions=record['medical_conditions'],
                dietary_preferences=record['dietary_preferences'],
                social_media_handles=record['social_media_handles'],
                profession_category=record['profession_category'],
                volunteer_interests=record['volunteer_interests']
            )
            db.session.add(member)
        
        db.session.commit()

if __name__ == '__main__':
    init_db_with_sample_data()
