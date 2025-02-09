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

def generate_sample_data(count=50):
    return [generate_member() for _ in range(count)]

if __name__ == "__main__":
    data = generate_sample_data(50)
    with open("sample_data.json", "w") as f:
        json.dump(data, f, indent=2)
