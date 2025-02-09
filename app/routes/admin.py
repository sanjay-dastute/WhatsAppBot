# Author: SANJAY KR
from flask import Blueprint, request, jsonify, send_file, render_template, current_app
from ..models.family import Samaj, Member, Family
from ..controllers.admin_controller import (
    get_members, get_samaj_list, get_member,
    export_members_csv, get_family_members,
    get_family_summary
)
from io import StringIO
from ..utils.auth import login_required
from .. import db

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/dashboard", methods=["GET"])
def dashboard():
    return render_template("admin/dashboard.html")

@admin_bp.route("/members", methods=["GET"])
@login_required
def list_members():
    try:
        filters = {
            "samaj_name": request.args.get("samaj_name"),
            "family_name": request.args.get("family_name"),
            "name": request.args.get("name"),
            "role": request.args.get("role"),
            "age_min": request.args.get("age_min"),
            "age_max": request.args.get("age_max"),
            "blood_group": request.args.get("blood_group"),
            "city": request.args.get("city"),
            "profession": request.args.get("profession"),
            "is_family_head": request.args.get("is_family_head", type=bool)
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        members = get_members(db.session, filters)
        return jsonify([{
            "id": member.id,
            "samaj": member.samaj.name,
            "family": member.family.name,
            "name": member.name,
            "role": member.family_role,
            "age": member.age,
            "blood_group": member.blood_group,
            "mobile": member.mobile_1,
            "email": member.email,
            "city": member.current_city,
            "profession": member.profession_category,
            "is_family_head": member.is_family_head
        } for member in members])
    except Exception as e:
        current_app.logger.error(f"Error in list_members: {str(e)}")
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/samaj", methods=["GET"])
@login_required
def list_samaj():
    try:
        samaj_list = get_samaj_list(db.session)
        return jsonify([{
            "id": samaj.id,
            "name": samaj.name,
            "family_count": len(samaj.families),
            "member_count": len(samaj.members),
            "created_at": samaj.created_at
        } for samaj in samaj_list])
    except Exception as e:
        current_app.logger.error(f"Error in list_samaj: {str(e)}")
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/families/summary", methods=["GET"])
@login_required
def list_families():
    try:
        filters = {
            "samaj_name": request.args.get("samaj_name"),
            "family_name": request.args.get("family_name")
        }
        filters = {k: v for k, v in filters.items() if v is not None}
        families = get_family_summary(db.session, filters)
        return jsonify(families)
    except Exception as e:
        current_app.logger.error(f"Error in list_families: {str(e)}")
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/families/<int:family_id>/members", methods=["GET"])
@login_required
def get_family_members_list(family_id: int):
    try:
        members = get_family_members(family_id, db.session)
        return jsonify([{
            "id": member.id,
            "name": member.name,
            "role": member.family_role,
            "age": member.age,
            "is_family_head": member.is_family_head,
            "mobile": member.mobile_1,
            "email": member.email
        } for member in members])
    except Exception as e:
        current_app.logger.error(f"Error in get_family_members_list: {str(e)}")
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/members/<int:member_id>", methods=["GET"])
@login_required
def get_member_details(member_id: int):
    try:
        member = get_member(member_id, db.session)
        if not member:
            return jsonify({"error": "Member not found"}), 404
        
        member_data = {
            "id": member.id,
            "name": member.name,
            "family_role": member.family_role,
            "age": member.age,
            "blood_group": member.blood_group,
            "mobile_1": member.mobile_1,
            "mobile_2": member.mobile_2,
            "email": member.email,
            "education": member.education,
            "occupation": member.occupation,
            "marital_status": member.marital_status,
            "address": member.address,
            "birth_date": str(member.birth_date) if member.birth_date else None,
            "anniversary_date": str(member.anniversary_date) if member.anniversary_date else None,
            "native_place": member.native_place,
            "current_city": member.current_city,
            "languages_known": member.languages_known,
            "skills": member.skills,
            "hobbies": member.hobbies,
            "emergency_contact": member.emergency_contact,
            "relationship_status": member.relationship_status,
            "medical_conditions": member.medical_conditions,
            "dietary_preferences": member.dietary_preferences,
            "social_media_handles": member.social_media_handles,
            "profession_category": member.profession_category,
            "volunteer_interests": member.volunteer_interests,
            "is_family_head": member.is_family_head,
            "samaj": member.samaj.name,
            "family": member.family.name
        }
        return jsonify(member_data)
    except Exception as e:
        current_app.logger.error(f"Error in get_member_details: {str(e)}")
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/export/csv", methods=["GET"])
@login_required
def export_csv():
    try:
        filters = {
            "samaj_name": request.args.get("samaj_name"),
            "family_name": request.args.get("family_name"),
            "name": request.args.get("name"),
            "role": request.args.get("role"),
            "city": request.args.get("city"),
            "profession": request.args.get("profession")
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        csv_data, filename = export_members_csv(db.session, filters)
        
        from io import BytesIO
        output = BytesIO()
        output.write(csv_data.encode('utf-8'))
        output.seek(0)
        
        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        current_app.logger.error(f"Error in export_csv: {str(e)}")
        return jsonify({"error": str(e)}), 500
