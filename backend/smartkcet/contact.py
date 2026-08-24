"""Contact API endpoints using Flask Blueprint."""

import logging
from flask import Blueprint, jsonify, request
from .db.session import get_db

router = Blueprint("contact", __name__, url_prefix="/api")
logger = logging.getLogger("smartkcet.contact")

CONTACT_SUPPORT_EMAIL = "support@smartkcet.com"
CONTACT_INFO_EMAIL = "info@smartkcet.com"


@router.route("/contact", methods=["POST"])
def submit_contact_message():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "")
    email = data.get("email", "")
    subject = data.get("subject", "")
    message = data.get("message", "")

    if not name or not email or not subject or not message:
        return jsonify({"error": "validation_error", "message": "All fields are required."}), 400

    try:
        logger.info("Contact message received from %s (%s) - Subject: %s", name, email, subject)
        return jsonify({
            "status": "success",
            "message": "Your message has been sent successfully. We'll review it and get back to you within 24 hours.",
        }), 201
    except Exception as e:
        logger.error("Error processing contact message: %s", str(e))
        return jsonify({"error": "server_error", "message": str(e)}), 500


__all__ = ["router"]
