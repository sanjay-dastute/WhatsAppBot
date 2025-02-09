# Author: SANJAY KR
import os
from sqlalchemy.orm import Session
from flask import current_app
from ..models.family import Samaj, Member, Family
from ..services.whatsapp_service import get_whatsapp_service
from twilio.base.exceptions import TwilioRestException

def get_service():
    try:
        return get_whatsapp_service()
    except RuntimeError:
        current_app.logger.error("WhatsApp service not initialized")
        return None

def handle_webhook(phone_number: str, message: str, db: Session):
    try:
        # Initialize WhatsApp service
        whatsapp_service = get_service()
        if whatsapp_service is None:
            return "Service temporarily unavailable. Please try again later.", False

        if not whatsapp_service.client:
            current_app.logger.error("Twilio client not properly initialized")
            return "Service temporarily unavailable. Please try again later.", False

        # Validate input parameters
        if not phone_number or not message:
            current_app.logger.error(f"Missing required parameters: phone={phone_number}, message={message}")
            return "Invalid request format. Please try again.", False

        phone_number = phone_number.replace("whatsapp:", "").strip()
        if not phone_number.startswith("+"):
            phone_number = "+" + phone_number

        if not phone_number[1:].isdigit() or len(phone_number) < 10:
            current_app.logger.error(f"Invalid phone number format: {phone_number}")
            return "Invalid phone number format. Please try again.", False

        system_number = os.getenv("TWILIO_PHONE_NUMBER", "").replace("whatsapp:", "")
        if phone_number == system_number:
            current_app.logger.error(f"Received message from system number: {phone_number}")
            return "Cannot process messages from the system number.", False

        current_app.logger.info(f"Processing webhook for {phone_number}: {message}")

        session = whatsapp_service.current_sessions.get(phone_number, {})
        if not session or session.get("step", 0) < 26:
            response, success = whatsapp_service.handle_message(
                phone_number=phone_number,
                message=message,
                db=db
            )
            if not success:
                current_app.logger.error(f"Failed to process message from {phone_number}")
                return response, False

            try:
                if not whatsapp_service.send_message(phone_number, response):
                    current_app.logger.error(f"Failed to send WhatsApp message to {phone_number}")
                    return "Failed to send response message", False
                return response, True
            except Exception as e:
                current_app.logger.error(f"Error sending message to {phone_number}: {str(e)}")
                return "Failed to send response message", False
            
        # Clean up phone number and validate format
        phone_number = phone_number.replace("whatsapp:", "").strip()
        if not phone_number.startswith("+"):
            phone_number = "+" + phone_number
            
        if not phone_number[1:].isdigit() or len(phone_number) < 10:
            current_app.logger.error(f"Invalid phone number format: {phone_number}")
            return "Invalid phone number format. Please try again.", False
            
        # Check if this is the system number
        system_number = os.getenv("TWILIO_PHONE_NUMBER", "").replace("whatsapp:", "")
        if phone_number == system_number:
            current_app.logger.error(f"Received message from system number: {phone_number}")
            return "Cannot process messages from the system number.", False
            
        current_app.logger.info(f"Processing webhook for {phone_number}: {message}")
        
        # Process the message using environment variables for configuration
        response, success = whatsapp_service.handle_message(
            phone_number=phone_number,
            message=message,
            db=db
        )
        if not success:
            current_app.logger.error(f"Failed to process message from {phone_number}")
            return response, False
            
        # Send response message
        try:
            if not whatsapp_service.send_message(phone_number, response):
                current_app.logger.error(f"Failed to send WhatsApp message to {phone_number}")
                return "Failed to send response message", False
        except Exception as e:
            current_app.logger.error(f"Error sending message to {phone_number}: {str(e)}")
            return "Failed to send response message", False
            
        # Get session data and process if needed
        # Process completed session data if available
        data = session.get("data", {})
        family_context = session.get("family_context", {})
        
        if not data or not family_context:
            current_app.logger.error("Missing session data or family context")
            return "Session expired. Please start over by sending 'Start'.", False
            
            try:
                samaj = db.query(Samaj).filter(Samaj.name == data["samaj"]).first()
                if not samaj:
                    samaj = Samaj(name=data["samaj"])
                    db.add(samaj)
                    db.flush()
                    current_app.logger.info(f"Created new Samaj: {data['samaj']}")
                
                family_role = data.get("family_role", "").title()
                is_head = family_role == "Head"
                
                if is_head:
                    family_name = f"{data['name']}'s Family"
                    existing_family = db.query(Family).filter(
                        Family.name == family_name,
                        Family.samaj_id == samaj.id
                    ).first()
                    
                    if existing_family:
                        raise ValueError(
                            f"A family with name '{family_name}' already exists in "
                            f"{data['samaj']} Samaj"
                        )
                    
                    family = Family(name=family_name, samaj_id=samaj.id)
                    db.add(family)
                    db.flush()
                    current_app.logger.info(
                        f"Created new family '{family_name}' in Samaj '{data['samaj']}'"
                    )
                else:
                    family_head_name = data.get("family_head")
                    if not family_head_name:
                        raise ValueError("Family head name is required for non-head members")
                    
                    existing_head = db.query(Member).join(Family).filter(
                        Member.name == family_head_name,
                        Member.is_family_head == True,
                        Member.samaj_id == samaj.id
                    ).first()
                    
                    if not existing_head:
                        raise ValueError(
                            f"Family head '{family_head_name}' not found in "
                            f"samaj '{data['samaj']}'"
                        )
                    
                    family = existing_head.family
                    current_app.logger.info(
                        f"Found existing family for head '{family_head_name}'"
                    )
            except Exception as e:
                current_app.logger.error(f"Error processing family data: {str(e)}")
                return str(e), False

            member = Member(
                samaj_id=samaj.id,
                family_id=family.id,
                is_family_head=is_head,
                name=data["name"],
                gender=data.get("gender"),
                age=int(data.get("age", 0)) if data.get("age") else None,
                blood_group=data.get("blood_group"),
                mobile_1=data.get("mobile_1"),
                mobile_2=data.get("mobile_2") if data.get("mobile_2") != "skip" else None,
                education=data.get("education"),
                occupation=data.get("occupation"),
                marital_status=data.get("marital_status"),
                address=data.get("address"),
                email=data.get("email"),
                birth_date=data.get("birth_date"),
                anniversary_date=data.get("anniversary_date") if data.get("anniversary_date") != "skip" else None,
                native_place=data.get("native_place"),
                current_city=data.get("current_city"),
                languages_known=data.get("languages_known"),
                skills=data.get("skills"),
                hobbies=data.get("hobbies"),
                emergency_contact=data.get("emergency_contact"),
                relationship_status=data.get("relationship_status"),
                family_role=family_role,
                medical_conditions=data.get("medical_conditions") if data.get("medical_conditions") != "skip" else None,
                dietary_preferences=data.get("dietary_preferences"),
                social_media_handles=data.get("social_media_handles") if data.get("social_media_handles") != "skip" else None,
                profession_category=data.get("profession_category"),
                volunteer_interests=data.get("volunteer_interests") if data.get("volunteer_interests") != "skip" else None
            )
                
                # Update family context with member info
                family_context["family_members"].append({
                    "name": member.name,
                    "role": member.family_role,
                    "is_head": member.is_family_head,
                    "age": member.age,
                    "relationship": member.relationship_status
                })
                
                # Validate and save member with family context
                try:
                    member.validate_family_role()
                    db.add(member)
                    db.flush()  # Get member ID before committing
                    
                    # Update family context with member info
                    family_context["family_members"].append({
                        "id": member.id,
                        "name": member.name,
                        "role": member.family_role,
                        "is_head": member.is_family_head,
                        "age": member.age,
                        "relationship": member.relationship_status
                    })
                    
                    if member.is_family_head:
                        family.head_of_family_id = member.id
                        family_context["family_head_id"] = member.id
                        family_context["family_head"] = member.name
                    
                    db.commit()
                    current_app.logger.info(
                        f"Successfully saved member {member.name} (ID: {member.id}) "
                        f"in family {family.name} with role {member.family_role}"
                    )
                    
                    # Clear session after successful save
                    del whatsapp_service.current_sessions[phone_number]
                    return "Your information has been successfully saved. Thank you!", True
                    
                except ValueError as e:
                    current_app.logger.error(f"Family role validation failed: {str(e)}")
                    db.rollback()
                    return str(e), False
                except Exception as e:
                    current_app.logger.error(f"Database error: {str(e)}")
                    db.rollback()
                    return "An error occurred while saving your information. Please try again.", False
                
        except Exception as e:
            current_app.logger.error(f"Error processing data: {str(e)}")
            return "An error occurred while processing your information. Please try again.", False
            
    except Exception as e:
        current_app.logger.error(f"Unexpected error in webhook: {str(e)}")
        return "An unexpected error occurred. Please try again by sending 'Start'.", False
