# Author: SANJAY KR
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from flask import current_app, has_app_context, Flask
import os
from dotenv import load_dotenv
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session

load_dotenv()

_instance = None

def get_whatsapp_service():
    if not has_app_context():
        raise RuntimeError("No Flask application context")
    
    app = current_app._get_current_object()
    if not hasattr(app, 'extensions'):
        app.extensions = {}
    if 'whatsapp_service' not in app.extensions:
        service = WhatsAppService()
        service.init_app(app)
    return app.extensions['whatsapp_service']

class WhatsAppService:
    def __init__(self):
        self.current_sessions: Dict[str, Dict[str, Any]] = {}
        self.client = None
        self._dev_session: Optional[Dict[str, Any]] = None
        self.db = None
        self.dev_mode = False
        self.phone_number: Optional[str] = None
        
    def _create_session(self, phone_number: str, message: str) -> Dict[str, Any]:
        if not phone_number or not message:
            raise ValueError("Phone number and message are required")
            
        # Clean up phone number format
        phone_number = phone_number.replace("whatsapp:", "").strip()
        if not phone_number.startswith("+"):
            phone_number = "+" + phone_number
            
        # Initialize session with proper typing
        session: Dict[str, Any] = {
            "step": 0 if message.lower() == "start" else -1,
            "data": {},
            "phone_number": phone_number,
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "family_context": {
                "family_members": [],
                "family_roles": {},
                "is_new_family": False,
                "role_confirmed": False,
                "samaj_name": None,
                "samaj_id": None,
                "family_id": None,
                "family_head": None,
                "family_head_id": None,
                "validation_errors": [],
                "creation_time": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
        # Store session based on mode
        if self.dev_mode:
            self._dev_session = session
        else:
            self.current_sessions[phone_number] = session
            
        current_app.logger.info(f"Created new session for {phone_number} with step {session['step']}")
        return session
        
    def save_member_data(self, data: Dict[str, Any], phone_number: str, db: Session) -> Tuple[bool, str]:
        """Save member data with proper family organization"""
        try:
            from ..models.family import Samaj, Family, Member
            
            if not db:
                current_app.logger.error("Database session not provided")
                return False, "Database error. Please try again later."
            
            session: Session = db
            
            # Get or create Samaj within transaction
            samaj = session.query(Samaj).filter_by(name=data["samaj"]).first()
            if not samaj:
                samaj = Samaj(name=data["samaj"])
                session.add(samaj)
                session.flush()
            
            family_role = data.get("family_role", "").title()
            
            # Handle family creation/lookup within transaction
            if self.dev_mode:
                if not self._dev_session:
                    current_app.logger.error("Dev session not initialized")
                    return False, "Session error. Please try again."
                family_context = self._dev_session.get("family_context", {})
            else:
                if phone_number not in self.current_sessions:
                    current_app.logger.error(f"No session found for {phone_number}")
                    return False, "Session expired. Please start over."
                family_context = self.current_sessions[phone_number].get("family_context", {})
            current_app.logger.info(f"Processing family context: {family_context}")
            
            if family_role == "Head":
                if not family_context.get("is_new_family"):
                    current_app.logger.error("Invalid family context for head role")
                    return False, "Error: Invalid family context for head role"
                    
                family = Family(
                    name=family_context.get("family_name", f"{data['name']}'s Family"),
                    samaj_id=samaj.id
                )
                session.add(family)
                session.flush()
                current_app.logger.info(
                    f"Created new family: {family.name} in Samaj: {samaj.name}"
                )
            else:
                if family_context.get("is_new_family"):
                    current_app.logger.error("Invalid family context for non-head role")
                    return False, "Error: Invalid family context for non-head role"
                    
                # Find family by head's name with validation
                current_app.logger.info(
                    f"Looking up family by head: {data['family_head']} in Samaj: {samaj.name}"
                )
                family = session.query(Family).join(Member).filter(
                    Member.name == data['family_head'],
                    Member.is_family_head == True,
                    Family.samaj_id == samaj.id
                ).first()
                
                if not family:
                    current_app.logger.error(
                        f"Family head not found: {data['family_head']} in Samaj: {samaj.name}"
                    )
                    return False, "Error: Family head not found. Please try again."
                    
                current_app.logger.info(
                    f"Found family: {family.name} with head: {data['family_head']}"
                )
                    
                # Validate family role constraints with comprehensive logging
                current_app.logger.info(f"Validating family role constraints for {family_role}")
                existing_roles = session.query(Member.family_role, Member.name).filter(
                    Member.family_id == family.id
                ).all()
                
                # Count roles and store names
                role_counts = {}
                role_names = {}
                for role, name in existing_roles:
                    role_counts[role] = role_counts.get(role, 0) + 1
                    if role not in role_names:
                        role_names[role] = []
                    role_names[role].append(name)
                
                current_app.logger.info(
                    f"Existing roles in family {family.name}: "
                    f"{', '.join([f'{role}({count})' for role, count in role_counts.items()])}"
                )
                
                # Validate role-specific constraints
                if family_role == "Spouse":
                    if role_counts.get("Spouse", 0) > 0:
                        current_app.logger.error(
                            f"Cannot add spouse {data['name']}: Family already has spouse {role_names['Spouse'][0]}"
                        )
                        return False, "Error: Family already has a spouse member"
                elif family_role == "Parent":
                    if role_counts.get("Parent", 0) >= 2:
                        current_app.logger.error(
                            f"Cannot add parent {data['name']}: Family already has maximum parents "
                            f"({', '.join(role_names['Parent'])})"
                        )
                        return False, "Error: Family cannot have more than two parents"
                elif family_role == "Child":
                    if not any(role in ["Head", "Spouse", "Parent"] for role in role_counts.keys()):
                        current_app.logger.error(
                            f"Cannot add child {data['name']}: Family must have at least one parent figure"
                        )
                        return False, "Error: Family must have at least one parent figure to add a child"
                elif family_role == "Sibling":
                    if "Head" not in role_counts:
                        current_app.logger.error(
                            f"Cannot add sibling {data['name']}: Family must have a head member"
                        )
                        return False, "Error: Family must have a head member to add a sibling"
            
            # Create member record within transaction
            try:
                # Get the appropriate session based on mode
                if self.dev_mode:
                    current_session = self._dev_session
                else:
                    current_session = self.current_sessions[phone_number]
                
                # Validate family context with comprehensive checks
                if not current_session:
                    current_app.logger.error("Session not found")
                    return False, "Session error. Please try again."
                    
                family_context = current_session.get("family_context", {})
                current_app.logger.info(f"Validating family context before member creation: {family_context}")
                
                if not family_context or not family_context.get("role_confirmed"):
                    current_app.logger.error("Family role not confirmed in context")
                    raise ValueError("Family role not confirmed")
                
                # Update family context with current state
                family_context["samaj_id"] = samaj.id
                family_context["family_id"] = family.id
                family_context["last_updated"] = datetime.utcnow().isoformat()
                
                if family_role == "Head":
                    if not family_context.get("is_new_family"):
                        current_app.logger.error("Attempting to create head member without new family context")
                        raise ValueError("Invalid context for family head creation")
                    family_context["family_roles"] = {"Head": [data["name"]]}
                    family_context["family_members"].append({
                        "name": data["name"],
                        "role": "Head",
                        "is_head": True
                    })
                else:
                    # Update family context for non-head members
                    if family_role not in family_context["family_roles"]:
                        family_context["family_roles"][family_role] = []
                    family_context["family_roles"][family_role].append(data["name"])
                    family_context["family_members"].append({
                        "name": data["name"],
                        "role": family_role,
                        "is_head": False
                    })
                
                if self.dev_mode:
                    if self._dev_session is None:
                        self._dev_session = {"family_context": family_context}
                    else:
                        self._dev_session["family_context"] = family_context
                else:
                    if phone_number not in self.current_sessions:
                        self.current_sessions[phone_number] = {"family_context": family_context}
                    else:
                        self.current_sessions[phone_number]["family_context"] = family_context
                current_app.logger.info(
                    f"Updated family context: roles={family_context['family_roles']}, "
                    f"members={len(family_context['family_members'])}"
                )

                # Log family relationship details
                current_app.logger.info(
                    f"Creating member record with family relationships: "
                    f"samaj={samaj.name}, "
                    f"family={family.name}, "
                    f"role={family_role}, "
                    f"is_head={data.get('is_family_head', False)}"
                )
                
                # Create member with family context
                member = Member(
                    name=data['name'],
                    family_id=family.id,
                    samaj_id=samaj.id,
                    family_role=family_role,
                    is_family_head=data.get('is_family_head', False),
                    gender=data.get('gender'),
                    age=int(data.get('age', 0)) if data.get('age') else None,
                    blood_group=data.get('blood_group'),
                    mobile_1=data.get('mobile_1'),
                    mobile_2=data.get('mobile_2') if data.get('mobile_2') != 'skip' else None,
                    education=data.get('education'),
                    occupation=data.get('occupation'),
                    marital_status=data.get('marital_status'),
                    address=data.get('address'),
                    email=data.get('email'),
                    birth_date=data.get('birth_date'),
                    anniversary_date=data.get('anniversary_date') if data.get('anniversary_date') != 'skip' else None,
                    native_place=data.get('native_place'),
                    current_city=data.get('current_city'),
                    languages_known=data.get('languages_known'),
                    skills=data.get('skills'),
                    hobbies=data.get('hobbies'),
                    emergency_contact=data.get('emergency_contact'),
                    relationship_status=data.get('relationship_status'),
                    medical_conditions=data.get('medical_conditions') if data.get('medical_conditions') != 'skip' else None,
                    dietary_preferences=data.get('dietary_preferences'),
                    social_media_handles=data.get('social_media_handles') if data.get('social_media_handles') != 'skip' else None,
                    profession_category=data.get('profession_category'),
                    volunteer_interests=data.get('volunteer_interests') if data.get('volunteer_interests') != 'skip' else None
                )
            
                # Validate and save member with family context
                member.validate_family_role()
                session.add(member)
                session.flush()  # Get member ID before committing
                
                if family_role == "Head":
                    family.head_of_family_id = member.id
                    family_context["family_head_id"] = member.id
                
                # Update family context with member ID and commit
                family_context["family_members"].append({
                    "id": member.id,
                    "name": member.name,
                    "role": member.family_role,
                    "is_head": member.is_family_head
                })
                session["family_context"] = family_context
                
                session.commit()
                current_app.logger.info(
                    f"Successfully saved member {member.name} (ID: {member.id}) "
                    f"in family {family.name} with role {member.family_role}"
                )
                
                # Clear session after successful save
                if self.dev_mode:
                    self._dev_session = None
                else:
                    del self.current_sessions[phone_number]
                
                role_messages = {
                    "Head": f"head of {data['name']}'s family in {data['samaj']} Samaj",
                    "Spouse": f"spouse in {data['family_head']}'s family",
                    "Parent": f"parent in {data['family_head']}'s family",
                    "Child": f"child in {data['family_head']}'s family",
                    "Sibling": f"sibling in {data['family_head']}'s family",
                    "Other": f"member in {data['family_head']}'s family"
                }
                
                return True, f"Thank you! Your information has been saved. You are registered as the {role_messages[family_role]}."
            except Exception as e:
                session.rollback()
                current_app.logger.error(f"Error saving member data: {str(e)}")
                return False, f"Error saving data: {str(e)}"
                
        except Exception as e:
            current_app.logger.error(f"Failed to save member data: {str(e)}")
            return False, "An error occurred while saving your information. Please try again later."
        
    @classmethod
    def get_instance(cls):
        global _instance
        if _instance is None:
            _instance = cls()
        return _instance
        
    def init_app(self, app):
        try:
            # Check if service is already initialized
            if hasattr(app, 'extensions') and 'whatsapp_service' in app.extensions:
                return app.extensions['whatsapp_service']
                
            from .. import db
            self.db = db
            
            # Ensure database tables exist
            with app.app_context():
                self.db.create_all()
                
            self.dev_mode = os.getenv("FLASK_ENV") == "development"
            self.current_sessions = {}
            
            if self.dev_mode:
                app.logger.info("Initializing WhatsApp service in development mode")
                class MockTwilioClient:
                    class Messages:
                        def create(self, from_=None, body=None, to=None):
                            app.logger.info(f"[DEV] Sending message to {to}: {body}")
                            return True
                            
                    def __init__(self):
                        self.messages = self.Messages()
                        
                self.client = MockTwilioClient()
                self.phone_number = "whatsapp:+14155238886"
                self._dev_session = {
                    "step": -1,
                    "data": {},
                    "family_context": {
                        "family_members": [],
                        "family_roles": {},
                        "is_new_family": False,
                        "role_confirmed": False
                    }
                }
                if not hasattr(app, 'extensions'):
                    app.extensions = {}
                app.extensions['whatsapp_service'] = self
                app.logger.info("Development mode initialized with mock sessions")
                return self
                
            account_sid = os.getenv("TWILIO_ACCOUNT_SID", "ACfe44f5cbbed573f96f4ebe029402aeea")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN", "2a84904c3e83f9309673fd4cc910e2c4")
            
            if not account_sid or not auth_token:
                app.logger.error("Twilio credentials not properly configured")
                raise ValueError("Twilio credentials not properly configured")
                
            self.client = Client(account_sid, auth_token)
            self.phone_number = os.getenv("TWILIO_PHONE_NUMBER", "whatsapp:+14155238886")
            
            # Validate phone number format
            if not self.phone_number.startswith("whatsapp:+"):
                self.phone_number = f"whatsapp:+{self.phone_number.lstrip('+')}"
            
            # Test Twilio connection
            try:
                self.client.api.accounts(account_sid).fetch()
                app.logger.info(f"Successfully connected to Twilio account {account_sid}")
            except Exception as e:
                app.logger.error(f"Failed to connect to Twilio: {str(e)}")
                raise ValueError("Failed to validate Twilio credentials")
            
            # Store instance in app context
            if not hasattr(app, 'extensions'):
                app.extensions = {}
            app.extensions['whatsapp_service'] = self
            
            app.logger.info(f"WhatsApp service initialized successfully with number {self.phone_number}")
            return self
        except Exception as e:
            app.logger.error(f"Failed to initialize WhatsApp service: {str(e)}")
            raise

    def send_message(self, to: str, message: str) -> bool:
        try:
            if not self.client:
                current_app.logger.error("Twilio client not initialized")
                return False
                
            system_number = os.getenv("TWILIO_PHONE_NUMBER", "whatsapp:+14155238886")
            
            # Clean up and format the destination number for WhatsApp
            to_number = to.strip().replace(" ", "").replace("whatsapp:", "")
            if not to_number.startswith("+"):
                to_number = "+" + to_number
                
            # Validate number format (must be E.164 format with country code)
            if not to_number.startswith("+") or not to_number[1:].isdigit() or len(to_number) < 10:
                current_app.logger.error(f"Invalid phone number format: {to_number}")
                return False
                
            # Format for WhatsApp API
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"
                
            # Ensure system number is properly formatted
            if not system_number.startswith("whatsapp:"):
                system_number = f"whatsapp:{system_number}"
                
            # Check if trying to send to system number
            if to_number.replace("whatsapp:", "") == system_number.replace("whatsapp:", ""):
                current_app.logger.error(f"Cannot send message to system number: {to_number}")
                return False
                
            try:
                current_app.logger.info(f"Attempting to send message from {system_number} to {to_number}")
                self.client.messages.create(
                    from_=system_number,
                    body=message,
                    to=to_number
                )
                current_app.logger.info(f"Successfully sent message to {to_number}")
                return True
            except Exception as e:
                current_app.logger.error(f"Failed to send WhatsApp message: {str(e)}")
                if "Unable to create record" in str(e):
                    sandbox_code = os.getenv("TWILIO_SANDBOX_CODE", "hello")
                    error_msg = (
                        f"This number is not registered in the WhatsApp sandbox. "
                        f"Please send 'join {sandbox_code}' to {system_number.replace('whatsapp:', '')} "
                        "to start using the bot."
                    )
                    current_app.logger.error(error_msg)
                    return False
                elif "is not a valid phone number" in str(e):
                    current_app.logger.error(f"Invalid phone number format: {to_number}")
                    return False
                return False
        except TwilioRestException as e:
            if "same To and From" in str(e):
                current_app.logger.error(f"Cannot send message to system number: {to_number}")
                return False
            current_app.logger.error(f"Twilio API error: {str(e)}")
            return False
        except Exception as e:
            current_app.logger.error(f"Failed to send WhatsApp message: {str(e)}")
            return False

    def validate_field(self, value: str, field: str) -> bool:
        """Simplified validation for optional fields"""
        if value.lower() == "skip" and field in ["mobile_2", "anniversary_date", "medical_conditions", "social_media_handles", "volunteer_interests"]:
            return True
        return bool(value.strip())
        
    def validate_input(self, field: str, value: str) -> tuple[bool, str]:
        current_app.logger.debug(f"Validating field '{field}' with value '{value}'")
        value = value.strip()
        validations = {
            "gender": lambda x: x.lower() in ["male", "female", "other"],
            "age": lambda x: x.isdigit() and 0 <= int(x) <= 120,
            "blood_group": lambda x: x.replace(" ", "").upper() in ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
            "mobile_1": lambda x: x.isdigit() and len(x) == 10,
            "mobile_2": lambda x: x.isdigit() and len(x) == 10 if x.lower() != "skip" else True,
            "email": lambda x: "@" in x and "." in x.split("@")[1],
            "birth_date": lambda x: len(x.split("/")) == 3,
            "anniversary_date": lambda x: len(x.split("/")) == 3 if x.lower() != "skip" else True,
            "emergency_contact": lambda x: x.isdigit() and len(x) == 10,
            "family_role": lambda x: x.title() in ["Head", "Spouse", "Child", "Parent", "Sibling", "Other"],
            "family_head": lambda x: bool(x.strip()),
            "marital_status": lambda x: x.title() in ["Single", "Married", "Divorced", "Widowed"],
            "relationship_status": lambda x: x.title() in ["Single", "Married", "Divorced", "Widowed", "Other"],
            "medical_conditions": lambda x: bool(x.strip()) if x.lower() != "skip" else True,
            "dietary_preferences": lambda x: bool(x.strip()),
            "social_media_handles": lambda x: bool(x.strip()) if x.lower() != "skip" else True,
            "volunteer_interests": lambda x: bool(x.strip()) if x.lower() != "skip" else True,
            "samaj": lambda x: bool(x.strip()) and len(x.strip()) >= 2,
            "name": lambda x: bool(x.strip()) and len(x.strip()) >= 2,
            "education": lambda x: bool(x.strip()),
            "occupation": lambda x: bool(x.strip()),
            "address": lambda x: bool(x.strip()),
            "native_place": lambda x: bool(x.strip()),
            "current_city": lambda x: bool(x.strip()),
            "languages_known": lambda x: bool(x.strip()),
            "skills": lambda x: bool(x.strip()),
            "hobbies": lambda x: bool(x.strip()),
            "profession_category": lambda x: bool(x.strip())
        }
        
        if field == "family_role":
            role = value.title()
            if role not in ["Head", "Spouse", "Child", "Parent", "Sibling", "Other"]:
                return False, "Please enter a valid role (Head/Spouse/Child/Parent/Sibling/Other)"
            return True, role
        
        if field not in validations:
            return True, value
            
        is_valid = validations[field](value)
        error_messages = {
            "gender": "Please enter Male, Female, or Other",
            "age": "Please enter a valid age between 0 and 120",
            "blood_group": "Please enter a valid blood group (A+, A-, B+, B-, AB+, AB-, O+, O-)",
            "mobile_1": "Please enter a valid 10-digit mobile number",
            "mobile_2": "Please enter a valid 10-digit mobile number or type 'skip'",
            "email": "Please enter a valid email address",
            "birth_date": "Please enter date in DD/MM/YYYY format",
            "anniversary_date": "Please enter date in DD/MM/YYYY format or type 'skip'",
            "emergency_contact": "Please enter a valid 10-digit contact number",
            "family_role": "Please enter a valid role (Head, Spouse, Child, Parent, Sibling, Other)",
            "family_head": "Please enter the family head's name",
            "marital_status": "Please enter a valid status (Single, Married, Divorced, Widowed)",
            "family_context": "Please provide valid family information"
        }
        
        return is_valid, error_messages[field] if not is_valid else value

    def handle_message(self, phone_number: str, message: str, db: Session) -> Tuple[str, bool]:
        try:
            if not phone_number or not message or not db:
                current_app.logger.error("Missing required parameters")
                return "Invalid request. Please try again.", False
                
            # Extract and format phone number
            phone_number = phone_number.replace("whatsapp:", "").strip()
            if not phone_number.startswith("+"):
                phone_number = "+" + phone_number
                
            current_app.logger.info(f"Processing message from {phone_number}: {message}")
            
            # Initialize or reset session on 'Start' command
            if message.lower() == "start":
                try:
                    session = self._create_session(phone_number, message)
                    current_app.logger.info(f"Created new session for {phone_number}")
                    return "Welcome to Family & Samaj Data Collection Bot!\nPlease enter your Samaj name:", True
                except Exception as e:
                    current_app.logger.error(f"Failed to create session: {str(e)}")
                    return "Failed to start session. Please try again.", False
                
            # Get or initialize session
            if self.dev_mode:
                if not self._dev_session:
                    self._dev_session = self._create_session(phone_number, message)
                session = self._dev_session
            else:
                if phone_number not in self.current_sessions:
                    self.current_sessions[phone_number] = self._create_session(phone_number, message)
                session = self.current_sessions[phone_number]
            
            # Handle sandbox join message
            if message.lower().startswith('join'):
                sandbox_code = message.split()[1] if len(message.split()) > 1 else None
                if sandbox_code:
                    current_app.logger.info(f"User {phone_number} joined sandbox with code: {sandbox_code}")
                    return "Welcome to the Family & Samaj Data Collection bot! Send 'Start' to begin.", True
                return "Please provide the sandbox code after 'join'. Example: 'join hello'", True
                
            # Check if this is the system number
            system_number = os.getenv("TWILIO_PHONE_NUMBER", "whatsapp:+14155238886").replace("whatsapp:", "")
            if phone_number == system_number:
                current_app.logger.error(f"Cannot process messages from system number: {phone_number}")
                return "Cannot process messages from the system number.", False
                
            if message.lower() == "start":
                session_data = {
                    "step": 0,
                    "data": {},
                    "family_context": {
                        "is_new_family": False,
                        "family_id": None,
                        "family_name": None,
                        "samaj_id": None,
                        "correction_mode": False,
                        "field_to_correct": None,
                        "pending_validation": [],
                        "role_confirmed": False,
                        "creation_time": datetime.utcnow().isoformat(),
                        "last_updated": datetime.utcnow().isoformat(),
                        "family_head": None,
                        "family_head_id": None,
                        "family_members": [],
                        "family_roles": {},
                        "validation_errors": []
                    }
                }
                current_app.logger.info(f"Initializing new session for {phone_number}")
                
                if self.dev_mode:
                    self._dev_session = session_data
                else:
                    self.current_sessions[phone_number] = session_data
                
                return "Welcome to Family & Samaj Data Collection Bot!\nPlease enter your Samaj name:", True
                
            # Get session and handle initialization
            session = self._dev_session if self.dev_mode else self.current_sessions.get(phone_number)
            if not session:
                if message.lower() != "start":
                    current_app.logger.warning(f"No active session for {phone_number}")
                    return "Please send 'Start' to begin the data collection process.", True
                session = self._create_session(phone_number, message)
                if self.dev_mode:
                    self._dev_session = session
                else:
                    self.current_sessions[phone_number] = session
                return "Welcome to Family & Samaj Data Collection Bot!\nPlease enter your Samaj name:", True
            
            step = session.get("step", -1)
            data = session.get("data", {})
            
            if step == -1 and message.lower() != "start":
                current_app.logger.warning(f"Invalid session state for {phone_number}")
                return "Please send 'Start' to begin.", True
                
            if step not in range(29) and message.lower() != "start":
                current_app.logger.error(f"Invalid step {step} for {phone_number}")
                return "Please send 'Start' to begin.", True
                
        except Exception as e:
            current_app.logger.error(f"Error accessing session data for {phone_number}: {str(e)}")
            return "Please send 'Start' to begin.", True
            
        if not session:
            return "Please send 'Start' to begin.", True
            
        data = session.get("data", {})

        steps = {
            0: ("samaj", "Please enter your full name:"),
            1: ("name", "Please enter your family role (Head/Spouse/Child/Parent/Sibling/Other):"),
            2: ("family_role", "Please enter your gender (Male/Female/Other):"),
            3: ("gender", "Please enter your age:"),
            4: ("age", "Please enter your blood group (A+/A-/B+/B-/AB+/AB-/O+/O-):"),
            5: ("blood_group", "Please enter your primary mobile number (10 digits):"),
            6: ("mobile_1", "Please enter your secondary mobile number (10 digits or type 'skip'):"),
            7: ("mobile_2", "Please enter your education:"),
            8: ("education", "Please enter your occupation:"),
            9: ("occupation", "Please enter your marital status (Single/Married/Divorced/Widowed):"),
            10: ("marital_status", "Please enter your address:"),
            11: ("address", "Please enter your email:"),
            12: ("email", "Please enter your birth date (DD/MM/YYYY):"),
            13: ("birth_date", "Please enter your anniversary date (DD/MM/YYYY or type 'skip'):"),
            14: ("anniversary_date", "Please enter your native place:"),
            15: ("native_place", "Please enter your current city:"),
            16: ("current_city", "Please enter languages known (comma-separated):"),
            17: ("languages_known", "Please enter your skills (comma-separated):"),
            18: ("skills", "Please enter your hobbies (comma-separated):"),
            19: ("hobbies", "Please enter emergency contact number (10 digits):"),
            20: ("emergency_contact", "Please enter your relationship status (Single/Married/Divorced/Widowed/Other):"),
            21: ("relationship_status", "Please enter any medical conditions (or type 'skip'):"),
            22: ("medical_conditions", "Please enter your dietary preferences:"),
            23: ("dietary_preferences", "Please enter your social media handles (or type 'skip'):"),
            24: ("social_media_handles", "Please enter your profession category:"),
            25: ("profession_category", "Please enter your volunteer interests (or type 'skip'):")
        }

        if step in steps:
            field, next_prompt = steps[step]
            is_valid, result = self.validate_input(field, message)
            if not is_valid:
                current_app.logger.warning(f"Invalid input for field '{field}' from {phone_number}: {message}")
                return result, True
                
            if message.lower() == "skip" and field in ["mobile_2", "anniversary_date", "medical_conditions", "social_media_handles", "volunteer_interests"]:
                data[field] = None
                current_app.logger.info(f"User {phone_number} skipped optional field '{field}'")
            else:
                data[field] = result
                current_app.logger.info(f"User {phone_number} provided valid input for '{field}': {result}")
                
                if field == "family_role":
                    family_role = result
                    current_app.logger.info(f"Processing family role: {family_role} for user {phone_number}")
                    
                    if family_role == "Head":
                        data["family_head"] = data.get("name", "")
                        data["is_family_head"] = True
                        session["family_context"] = {
                            "is_new_family": True,
                            "family_name": f"{data.get('name', '')}'s Family",
                            "role_confirmed": True,
                            "samaj_name": data.get("samaj"),
                            "samaj_id": None,
                            "family_id": None,
                            "family_head": data.get("name", ""),
                            "family_head_id": None,
                            "family_members": [{
                                "name": data.get("name", ""),
                                "role": "Head",
                                "is_head": True
                            }],
                            "family_roles": {"Head": [data.get("name", "")]},
                            "validation_errors": [],
                            "creation_time": datetime.utcnow().isoformat(),
                            "last_updated": datetime.utcnow().isoformat()
                        }
                    else:
                        data["is_family_head"] = False
                        session["family_context"] = {
                            "is_new_family": False,
                            "role_confirmed": True,
                            "samaj_name": data.get("samaj"),
                            "samaj_id": None,
                            "family_id": None,
                            "member_role": family_role,
                            "family_head": None,
                            "family_head_id": None,
                            "family_members": [],
                            "family_roles": {},
                            "validation_errors": [],
                            "creation_time": datetime.utcnow().isoformat(),
                            "last_updated": datetime.utcnow().isoformat()
                        }
            
            session["step"] = step + 1
            session["data"] = data
            current_app.logger.info(f"Advanced session for {phone_number} to step {step + 1}")
            
            if step == 25:  # After collecting all data, show confirmation
                confirmation_message = "Please review your information:\n\n"
                confirmation_message += f"Samaj: {data.get('samaj', '')}\n"
                confirmation_message += f"Name: {data.get('name', '')}\n"
                confirmation_message += f"Role: {data.get('family_role', '')}\n"
                
                family_context = session.get("family_context", {})
                if data.get('family_role') == "Head":
                    confirmation_message += f"Family Name: {family_context.get('family_name', '')}\n"
                else:
                    confirmation_message += f"Family Head: {data.get('family_head', '')}\n"
                
                confirmation_message += "\nYour Details:\n"
                for field_name, value in data.items():
                    if value is not None and field_name not in ['samaj', 'name', 'family_role', 'family_head']:
                        confirmation_message += f"{field_name.replace('_', ' ').title()}: {value}\n"
                
                confirmation_message += "\nIs this information correct? (Yes/No)"
                session["step"] = 28  # Move directly to confirmation step
                session["data"] = data
                return confirmation_message, True
            
            return next_prompt.format(data) if "{}" in next_prompt else next_prompt, True
            
            if message.lower() == "skip" and field in ["mobile_2", "anniversary_date", "medical_conditions", "social_media_handles", "volunteer_interests"]:
                data[field] = None
                current_app.logger.info(f"User {phone_number} skipped optional field '{field}'")
            else:
                if field == "family_role":
                    family_role = result
                    current_app.logger.info(f"Processing family role: {family_role} for user {phone_number}")
                    
                    if family_role == "Head":
                        data["family_head"] = data.get("name", "")
                        data["is_family_head"] = True
                        session["family_context"] = {
                            "is_new_family": True,
                            "family_name": f"{data.get('name', '')}'s Family",
                            "role_confirmed": True,
                            "samaj_name": data.get("samaj"),
                            "samaj_id": None,
                            "family_id": None,
                            "family_head": data.get("name", ""),
                            "family_head_id": None,
                            "family_members": [{
                                "name": data.get("name", ""),
                                "role": "Head",
                                "is_head": True
                            }],
                            "family_roles": {"Head": [data.get("name", "")]},
                            "validation_errors": [],
                            "creation_time": datetime.utcnow().isoformat(),
                            "last_updated": datetime.utcnow().isoformat()
                        }
                        current_app.logger.info(
                            f"Created new family context for head: {data['name']} in {data.get('samaj')} "
                            f"with roles: {session['family_context']['family_roles']}"
                        )
                    else:
                        data["is_family_head"] = False
                        session["family_context"] = {
                            "is_new_family": False,
                            "role_confirmed": True,
                            "samaj_name": data.get("samaj"),
                            "samaj_id": None,
                            "family_id": None,
                            "member_role": family_role,
                            "family_head": None,
                            "family_head_id": None,
                            "family_members": [],
                            "family_roles": {},
                            "validation_errors": [],
                            "creation_time": datetime.utcnow().isoformat(),
                            "last_updated": datetime.utcnow().isoformat()
                        }
                        current_app.logger.info(f"Created family context for {family_role}: {data['name']} in {data.get('samaj')}")
                    
                    data[field] = family_role
                else:
                    data[field] = result
                current_app.logger.info(f"User {phone_number} provided valid input for '{field}': {result}")
                
            session["step"] = step + 1
            session["data"] = data
            current_app.logger.info(f"Advanced session for {phone_number} to step {step + 1}")
            
            if step + 1 == 26:  # Before confirmation step
                confirmation_message = "Please review your information:\n\n"
                confirmation_message += f"Samaj: {data.get('samaj', '')}\n"
                confirmation_message += f"Name: {data.get('name', '')}\n"
                confirmation_message += f"Role: {data.get('family_role', '')}\n"
                
                family_context = session.get("family_context", {})
                if data.get('family_role') == "Head":
                    confirmation_message += f"Family Name: {family_context.get('family_name', '')}\n"
                else:
                    confirmation_message += f"Family Head: {data.get('family_head', '')}\n"
                
                confirmation_message += "\nYour Details:\n"
                for field_name, value in data.items():
                    if value is not None and field_name not in ['samaj', 'name', 'family_role', 'family_head']:
                        confirmation_message += f"{field_name.replace('_', ' ').title()}: {value}\n"
                
                confirmation_message += "\nIs this information correct? (Yes/No)"
                session["step"] = step + 1
                session["data"] = data
                return confirmation_message, True
            
            session["step"] = step + 1
            session["data"] = data
            current_app.logger.info(f"Advanced session for {phone_number} to step {step + 1}")
            
            if step == 25:  # After collecting all data, show confirmation
                if message.lower() == "skip" or self.validate_field(message, "volunteer_interests"):
                    if message.lower() != "skip":
                        data["volunteer_interests"] = message
                    
                    confirmation_message = "Please review your information:\n\n"
                    confirmation_message += f"Samaj: {data.get('samaj', '')}\n"
                    confirmation_message += f"Name: {data.get('name', '')}\n"
                    confirmation_message += f"Role: {data.get('family_role', '')}\n"
                    
                    family_context = session.get("family_context", {})
                    if data.get('family_role') == "Head":
                        confirmation_message += f"Family Name: {family_context.get('family_name', '')}\n"
                    else:
                        confirmation_message += f"Family Head: {data.get('family_head', '')}\n"
                        if family_context.get("family_members"):
                            confirmation_message += "\nExisting Family Members:\n"
                            for member in family_context["family_members"]:
                                confirmation_message += f"- {member['name']} ({member['role']})\n"
                    
                    confirmation_message += "\nYour Details:\n"
                    for field_name, value in data.items():
                        if value is not None and field_name not in ['samaj', 'name', 'family_role', 'family_head']:
                            confirmation_message += f"{field_name.replace('_', ' ').title()}: {value}\n"
                    
                    confirmation_message += "\nIs this information correct? (Yes/No)"
                    session["step"] = 28  # Move directly to confirmation step
                    session["data"] = data
                    return confirmation_message, True
                return "Please enter valid volunteer interests or type 'skip':", True
            
            return next_prompt.format(data) if "{}" in next_prompt else next_prompt, True
                
                family_role = data.get("family_role", "").title()
                # Build confirmation message with family context
                confirmation_message = "Please review your information:\n\n"
                confirmation_message += f"Samaj: {data.get('samaj', '')}\n"
                confirmation_message += f"Name: {data.get('name', '')}\n"
                confirmation_message += f"Role: {family_role}\n"
                
                family_context = session.get("family_context", {})
                if family_role == "Head":
                    confirmation_message += f"Family Name: {family_context.get('family_name', '')}\n"
                else:
                    confirmation_message += f"Family Head: {data.get('family_head', '')}\n"
                    if family_context.get("family_members"):
                        confirmation_message += "\nExisting Family Members:\n"
                        for member in family_context["family_members"]:
                            confirmation_message += f"- {member['name']} ({member['role']})\n"
                
                confirmation_message += "\nYour Details:\n"
                for field, value in data.items():
                    if value is not None and field not in ['samaj', 'name', 'family_role', 'family_head']:
                        confirmation_message += f"{field.replace('_', ' ').title()}: {value}\n"
                
                confirmation_message += "\nIs this information correct? (Yes/No)"
                return confirmation_message, True
            return "Please enter valid volunteer interests or type 'skip':", True
            
        if step == 28:  # Confirmation step
            if message.lower() == "yes":
                try:
                    current_app.logger.info(f"User {phone_number} confirmed data: {data}")
                    family_context = session.get("family_context", {})
                    if not family_context.get("role_confirmed"):
                        return "Error: Family role not confirmed. Please start over.", False
                    
                    # Update family context with final state before saving
                    family_context["last_updated"] = datetime.utcnow().isoformat()
                    session["family_context"] = family_context
                    
                    # Log the complete data being saved
                    current_app.logger.info(
                        f"Saving data for {phone_number}:\n"
                        f"Role: {data.get('family_role')}\n"
                        f"Family Head: {data.get('family_head')}\n"
                        f"Family Context: {family_context}"
                    )
                    
                    current_app.logger.info(
                        f"Saving member data for {phone_number} with family context: "
                        f"role={data.get('family_role')}, "
                        f"is_head={data.get('is_family_head')}, "
                        f"samaj={data.get('samaj')}, "
                        f"family_head={data.get('family_head')}"
                    )
                    
                    success, response = self.save_member_data(data, phone_number, db)
                    if success:
                        current_app.logger.info(
                            f"Successfully saved member data for {phone_number} in "
                            f"{data.get('samaj')} Samaj, family head: {data.get('family_head')}"
                        )
                        if self.dev_mode:
                            self._dev_session = None
                        else:
                            del self.current_sessions[phone_number]
                    else:
                        current_app.logger.error(
                            f"Failed to save member data for {phone_number}: {response}"
                        )
                    return response, success
                except Exception as e:
                    current_app.logger.error(f"Failed to save user data: {str(e)}")
                    return "An error occurred while saving your information. Please try again later.", False
            elif message.lower() == "no":
                session["step"] = 29  # Correction step
                field_list = "\n".join([
                    f"{i+1}. {field.replace('_', ' ').title()}: {value}" 
                    for i, (field, value) in enumerate(data.items())
                    if field != "family_head" or data.get("family_role", "").title() != "Head"
                ])
                return f"Which field would you like to correct? Enter the number:\n{field_list}", True
            else:
                return "Please reply with 'Yes' to confirm or 'No' to make corrections.", True
                
        if step == 29:  # Field selection for correction
            try:
                field_index = int(message) - 1
                fields = [f for f in data.keys() if f != "family_head" or data.get("family_role", "").title() != "Head"]
                if 0 <= field_index < len(fields):
                    field_to_correct = fields[field_index]
                    session["correction_field"] = field_to_correct
                    session["step"] = 30
                    return f"Current value of {field_to_correct.replace('_', ' ').title()}: {data[field_to_correct]}\nPlease enter the new value:", True
                else:
                    return "Please enter a valid number from the list.", True
            except ValueError:
                return "Please enter a valid number from the list.", True
                
        if step == 30:  # Handling correction input
            field_to_correct = session.get("correction_field")
            if not field_to_correct:
                return "An error occurred during correction. Please start over.", False
                
            is_valid, result = self.validate_input(field_to_correct, message)
            if not is_valid:
                return result, True
                
            data[field_to_correct] = result
            session["step"] = 28  # Return to confirmation step
            session["data"] = data
            
            # Show updated information
            family_role = data.get("family_role", "").title()
            confirmation_message = "Field updated. Please review your information:\n\n"
            confirmation_message += f"Samaj: {data.get('samaj', '')}\n"
            confirmation_message += f"Name: {data.get('name', '')}\n"
            confirmation_message += f"Role: {family_role}\n"
            
            if family_role != "Head":
                confirmation_message += f"Family Head: {data.get('family_head', '')}\n"
            
            for field, value in data.items():
                if value is not None and field not in ['samaj', 'name', 'family_role', 'family_head']:
                    confirmation_message += f"{field.replace('_', ' ').title()}: {value}\n"
            
            confirmation_message += "\nIs this information correct? (Yes/No)"
            return confirmation_message, True
            
        # Default case - should never reach here
        current_app.logger.error(f"Invalid step encountered: {step}")
        return "Please send 'Start' to begin.", True
