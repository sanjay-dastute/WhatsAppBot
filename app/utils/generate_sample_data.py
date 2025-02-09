# Author: SANJAY KR
import random
from datetime import datetime, timedelta
import json

SAMAJ_CATEGORIES = ["Bhram", "Sindhi", "Maharashtra Mandal", "Vaishnav Vanik", "Lohana", "Bhatia", "Jain", "Patel", "Connected", "Marwari"]

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]

FIRST_NAMES = ["Raj", "Amit", "Priya", "Neha", "Suresh", "Ramesh", "Sanjay", "Vijay", "Meera", "Geeta", 
               "Rakesh", "Mukesh", "Seema", "Reena", "Anil", "Sunil", "Deepa", "Rekha", "Mohan", "Sohan"]

LAST_NAMES = ["Patel", "Shah", "Mehta", "Desai", "Joshi", "Bhatt", "Trivedi", "Pandya", "Vyas", "Pathak",
              "Kumar", "Singh", "Sharma", "Verma", "Gupta", "Malhotra", "Kapoor", "Khanna", "Chopra", "Reddy"]

def generate_phone():
    return f"+91{random.randint(7000000000, 9999999999)}"

def generate_member():
    gender = random.choice(["M", "F"])
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    
    return {
        "samaj": random.choice(SAMAJ_CATEGORIES),
        "name": f"{first_name} {random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')} {last_name}",
        "gender": gender,
        "age": random.randint(18, 80),
        "blood_group": random.choice(BLOOD_GROUPS),
        "mobile_1": generate_phone(),
        "mobile_2": generate_phone() if random.random() > 0.5 else None,
        "education": random.choice(["Graduate", "Post Graduate", "PhD", "High School", "Under Graduate"]),
        "occupation": random.choice(["Business", "Service", "Professional", "Student", "Retired"]),
        "marital_status": random.choice(["Single", "Married", "Widowed"]),
        "address": f"{random.randint(1, 999)}, Sample Street, City",
        "email": f"{first_name.lower()}.{last_name.lower()}@example.com",
        "birth_date": (datetime.now() - timedelta(days=random.randint(6570, 29200))).strftime("%Y-%m-%d"),
        "anniversary_date": (datetime.now() - timedelta(days=random.randint(365, 14600))).strftime("%Y-%m-%d") if random.random() > 0.3 else None,
        "native_place": random.choice(["Gujarat", "Maharashtra", "Rajasthan", "Delhi", "Karnataka"]),
        "current_city": random.choice(["Mumbai", "Delhi", "Bangalore", "Ahmedabad", "Pune"]),
        "languages_known": ", ".join(random.sample(["English", "Hindi", "Gujarati", "Marathi", "Sanskrit"], random.randint(2, 4))),
        "skills": ", ".join(random.sample(["Computer", "Management", "Teaching", "Writing", "Public Speaking"], random.randint(1, 3))),
        "hobbies": ", ".join(random.sample(["Reading", "Music", "Travel", "Cooking", "Photography"], random.randint(1, 3))),
        "emergency_contact": generate_phone(),
        "relationship_status": random.choice(["Married", "Single", "Widowed"]),
        "family_role": random.choice(["Head", "Spouse", "Child", "Parent"]),
        "medical_conditions": None if random.random() > 0.3 else random.choice(["None", "Diabetes", "Hypertension"]),
        "dietary_preferences": random.choice(["Vegetarian", "Jain", "Vegan"]),
        "social_media_handles": f"@{first_name.lower()}_{last_name.lower()}",
        "profession_category": random.choice(["IT", "Healthcare", "Education", "Business", "Finance"]),
        "volunteer_interests": ", ".join(random.sample(["Community Service", "Education", "Healthcare", "Environment"], random.randint(1, 3)))
    }

def generate_sample_data(db, count=50):
    from ..models.family import Samaj, Family, Member
    
    samaj_data = {}
    family_data = {}
    
    for samaj_name in SAMAJ_CATEGORIES[:count//5]:
        existing_samaj = db.query(Samaj).filter_by(name=samaj_name).first()
        if existing_samaj:
            samaj_data[samaj_name] = existing_samaj
            continue
            
        samaj = Samaj(name=samaj_name)
        db.add(samaj)
        db.flush()
        samaj_data[samaj_name] = samaj
        
        # Create 5 families per samaj
        for i in range(5):
            family_name = f"{samaj_name} Family {i+1}"
            family = Family(name=family_name, samaj_id=samaj.id)
            db.add(family)
            db.flush()
            family_data[family_name] = family
            
            # Generate family head
            head_data = generate_member()
            head = Member(
                samaj_id=samaj.id,
                family_id=family.id,
                is_family_head=True,
                name=head_data["name"],
                gender=head_data["gender"],
                age=head_data["age"],
                blood_group=head_data["blood_group"],
                mobile_1=head_data["mobile_1"],
                mobile_2=head_data["mobile_2"],
                education=head_data["education"],
                occupation=head_data["occupation"],
                marital_status=head_data["marital_status"],
                address=head_data["address"],
                email=head_data["email"],
                birth_date=head_data["birth_date"],
                anniversary_date=head_data["anniversary_date"],
                native_place=head_data["native_place"],
                current_city=head_data["current_city"],
                languages_known=head_data["languages_known"],
                skills=head_data["skills"],
                hobbies=head_data["hobbies"],
                emergency_contact=head_data["emergency_contact"],
                relationship_status=head_data["relationship_status"],
                family_role="Head",
                medical_conditions=head_data["medical_conditions"],
                dietary_preferences=head_data["dietary_preferences"],
                social_media_handles=head_data["social_media_handles"],
                profession_category=head_data["profession_category"],
                volunteer_interests=head_data["volunteer_interests"]
            )
            db.add(head)
            db.flush()
            
            # Update family head reference
            family.head_of_family_id = head.id
            db.flush()
            
            # Add 4 more members to each family
            for _ in range(4):
                member_data = generate_member()
                member = Member(
                    samaj_id=samaj.id,
                    family_id=family.id,
                    is_family_head=False,
                    name=member_data["name"],
                    gender=member_data["gender"],
                    age=member_data["age"],
                    blood_group=member_data["blood_group"],
                    mobile_1=member_data["mobile_1"],
                    mobile_2=member_data["mobile_2"],
                    education=member_data["education"],
                    occupation=member_data["occupation"],
                    marital_status=member_data["marital_status"],
                    address=member_data["address"],
                    email=member_data["email"],
                    birth_date=member_data["birth_date"],
                    anniversary_date=member_data["anniversary_date"],
                    native_place=member_data["native_place"],
                    current_city=member_data["current_city"],
                    languages_known=member_data["languages_known"],
                    skills=member_data["skills"],
                    hobbies=member_data["hobbies"],
                    emergency_contact=member_data["emergency_contact"],
                    relationship_status=member_data["relationship_status"],
                    family_role=random.choice(["Spouse", "Child", "Parent"]),
                    medical_conditions=member_data["medical_conditions"],
                    dietary_preferences=member_data["dietary_preferences"],
                    social_media_handles=member_data["social_media_handles"],
                    profession_category=member_data["profession_category"],
                    volunteer_interests=member_data["volunteer_interests"]
                )
                db.add(member)
            db.flush()
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

if __name__ == "__main__":
    data = generate_sample_data(50)
    with open("sample_data.json", "w") as f:
        json.dump(data, f, indent=2)
