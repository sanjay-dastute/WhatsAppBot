# Author: SANJAY KR
from flask import Blueprint, request, jsonify, current_app
import os
from sqlalchemy.orm import Session
from ..models.base import get_db
from ..controllers.whatsapp_controller import handle_webhook

whatsapp_bp = Blueprint("whatsapp", __name__)

@whatsapp_bp.route("/webhook", methods=["POST"])
def webhook():
    try:
        request_data = request.form
        if 'NumMedia' in request_data and int(request_data['NumMedia']) > 0:
            return jsonify({
                "success": False,
                "message": "Media attachments are not supported. Please send text messages only."
            }), 400

        phone_number = request_data.get("From", "").split(":")[-1].strip()
        if not phone_number.startswith("+"):
            phone_number = "+" + phone_number

        message = request_data.get("Body", "")
        current_app.logger.info(f"Received webhook: from={phone_number}, message={message}")

        db = get_db()
        response, success = handle_webhook(
            phone_number=phone_number,
            message=message,
            db=db
        )

        if os.getenv("FLASK_ENV") == "development":
            return jsonify({
                "success": True,
                "message": response,
                "debug_info": {
                    "phone": phone_number,
                    "original_message": message,
                    "processed": True
                }
            })

        # Create TwiML response for Twilio
        from twilio.twiml.messaging_response import MessagingResponse
        twiml = MessagingResponse()
        twiml.message(response)
        return str(twiml), 200, {'Content-Type': 'text/xml'}
    except Exception as e:
        current_app.logger.error(f"Webhook error: {str(e)}")
        # Create error TwiML response
        from twilio.twiml.messaging_response import MessagingResponse
        twiml = MessagingResponse()
        twiml.message("An error occurred. Please try again by sending 'Start'.")
        return str(twiml), 500, {'Content-Type': 'text/xml'}
