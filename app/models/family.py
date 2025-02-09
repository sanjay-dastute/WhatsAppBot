# Author: SANJAY KR
from .. import db
from sqlalchemy.orm import relationship
from sqlalchemy import event
from datetime import datetime

class Family(db.Model):
    __tablename__ = "family"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    samaj_id = db.Column(db.Integer, db.ForeignKey("samaj.id", ondelete="CASCADE"), nullable=False)
    head_of_family_id = db.Column(db.Integer, db.ForeignKey("member.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    members = relationship("Member", back_populates="family", foreign_keys="Member.family_id")
    samaj = relationship("Samaj", back_populates="families")

class Samaj(db.Model):
    __tablename__ = "samaj"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    families = relationship("Family", back_populates="samaj", cascade="all, delete-orphan")
    members = relationship("Member", back_populates="samaj", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Samaj {self.name}>"

class Member(db.Model):
    __tablename__ = "member"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    samaj_id = db.Column(db.Integer, db.ForeignKey("samaj.id", ondelete="CASCADE"), nullable=False)
    family_id = db.Column(db.Integer, db.ForeignKey("family.id", ondelete="CASCADE"), nullable=False)
    is_family_head = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10))
    age = db.Column(db.Integer)
    blood_group = db.Column(db.String(5))
    mobile_1 = db.Column(db.String(15))
    mobile_2 = db.Column(db.String(15))
    education = db.Column(db.String(100))
    occupation = db.Column(db.String(100))
    marital_status = db.Column(db.String(20))
    address = db.Column(db.String(200))
    email = db.Column(db.String(100))
    birth_date = db.Column(db.String(10))
    anniversary_date = db.Column(db.String(10))
    native_place = db.Column(db.String(100))
    current_city = db.Column(db.String(100))
    languages_known = db.Column(db.String(200))
    skills = db.Column(db.String(200))
    hobbies = db.Column(db.String(200))
    emergency_contact = db.Column(db.String(15))
    relationship_status = db.Column(db.String(20))
    family_role = db.Column(db.String(50))
    medical_conditions = db.Column(db.String(200))
    dietary_preferences = db.Column(db.String(100))
    social_media_handles = db.Column(db.String(200))
    profession_category = db.Column(db.String(100))
    volunteer_interests = db.Column(db.String(200))

    samaj = relationship("Samaj", back_populates="members")
    family = relationship("Family", back_populates="members", foreign_keys=[family_id])

    def validate_family_role(self):
        if not self.family_role:
            raise ValueError("Family role is required")
            
        if self.family_role == "Head" and not self.is_family_head:
            raise ValueError("Member with Head role must be marked as family head")
            
        # Check for existing family head
        if self.is_family_head:
            existing_head = Member.query.filter(
                Member.family_id == self.family_id,
                Member.is_family_head == True,
                Member.id != self.id
            ).first()
            if existing_head:
                raise ValueError(f"Family already has a head member: {existing_head.name}")
                
        # Get all existing family members and their roles
        existing_members = Member.query.filter(
            Member.family_id == self.family_id,
            Member.id != self.id
        ).all()
        
        # Count roles and store member details for validation messages
        role_counts = {}
        role_members = {}
        for member in existing_members:
            role = member.family_role
            role_counts[role] = role_counts.get(role, 0) + 1
            if role not in role_members:
                role_members[role] = []
            role_members[role].append(member)
            
        # Validate role-specific constraints with detailed error messages
        if self.family_role == "Spouse":
            if role_counts.get("Spouse", 0) > 0:
                spouse = role_members["Spouse"][0]
                raise ValueError(
                    f"Family already has a spouse member: {spouse.name} "
                    f"(age: {spouse.age}, relationship: {spouse.relationship_status})"
                )
                
        elif self.family_role == "Parent":
            if role_counts.get("Parent", 0) >= 2:
                parents = [f"{m.name} ({m.relationship_status})" for m in role_members["Parent"]]
                raise ValueError(
                    f"Family already has maximum parents: {', '.join(parents)}"
                )
                
        elif self.family_role == "Child":
            parent_roles = ["Head", "Spouse", "Parent"]
            has_parent = any(role_counts.get(role, 0) > 0 for role in parent_roles)
            if not has_parent:
                raise ValueError(
                    "Family must have at least one parent figure (Head/Spouse/Parent) "
                    "to add a child"
                )
                
        elif self.family_role == "Sibling":
            if "Head" not in role_counts:
                raise ValueError(
                    "Family must have a head member to add a sibling. "
                    "Please add the family head first."
                )
                
        # Additional validation for age-based relationships
        if self.age:
            if self.family_role == "Child":
                parent_members = []
                for role in ["Head", "Spouse", "Parent"]:
                    if role in role_members:
                        parent_members.extend(role_members[role])
                        
                for parent in parent_members:
                    if parent.age and parent.age <= self.age:
                        raise ValueError(
                            f"Child's age ({self.age}) cannot be greater than or equal to "
                            f"parent's age ({parent.age}, {parent.name})"
                        )
                        
            elif self.family_role == "Parent":
                children = role_members.get("Child", [])
                for child in children:
                    if child.age and child.age >= self.age:
                        raise ValueError(
                            f"Parent's age ({self.age}) cannot be less than or equal to "
                            f"child's age ({child.age}, {child.name})"
                        )

    def __repr__(self):
        return f"<Member {self.name} of {self.samaj.name if self.samaj else 'Unknown Samaj'}>"

@event.listens_for(Member, 'before_insert')
@event.listens_for(Member, 'before_update')
def validate_member(mapper, connection, target):
    target.validate_family_role()

@event.listens_for(Member, 'after_insert')
def update_family_head(mapper, connection, target):
    if target.is_family_head:
        connection.execute(
            Family.__table__.update().
            where(Family.id == target.family_id).
            values(head_of_family_id=target.id)
        )
