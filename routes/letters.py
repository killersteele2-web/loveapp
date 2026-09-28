from datetime import datetime

from flask import Blueprint, jsonify, request

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from models import (
    db,
    Letter,
    CoupleMember
)


letters_bp = Blueprint(
    "letters",
    __name__,
    url_prefix="/api/letters"
)


# ============================================================
# GET CURRENT USER'S COUPLE ID
# ============================================================

def get_user_couple_id():

    user_id = get_jwt_identity()

    membership = CoupleMember.query.filter_by(
        user_id=int(user_id)
    ).first()

    if not membership:
        return None

    return membership.couple_id


# ============================================================
# SERIALIZE LETTER
# ============================================================

def letter_to_dict(letter):

    return {
        "id": letter.id,
        "title": letter.title,
        "content": letter.content,
        "is_locked": letter.is_locked,

        "created_at": (
            letter.created_at.isoformat()
            if letter.created_at
            else None
        ),

        "updated_at": (
            letter.updated_at.isoformat()
            if letter.updated_at
            else None
        ),
    }


# ============================================================
# GET ALL LETTERS
# ============================================================

@letters_bp.route(
    "",
    methods=["GET"]
)
@jwt_required()
def get_letters():

    couple_id = get_user_couple_id()

    if not couple_id:
        return jsonify({
            "success": False,
            "message": "User is not connected to a couple."
        }), 403

    letters = (
        Letter.query
        .filter_by(
            couple_id=couple_id
        )
        .order_by(
            Letter.created_at.desc()
        )
        .all()
    )

    return jsonify({
        "success": True,
        "letters": [
            letter_to_dict(letter)
            for letter in letters
        ],
    }), 200


# ============================================================
# GET ONE LETTER
# ============================================================

@letters_bp.route(
    "/<int:letter_id>",
    methods=["GET"]
)
@jwt_required()
def get_letter(letter_id):

    couple_id = get_user_couple_id()

    if not couple_id:
        return jsonify({
            "success": False,
            "message": "User is not connected to a couple."
        }), 403

    letter = (
        Letter.query
        .filter_by(
            id=letter_id,
            couple_id=couple_id
        )
        .first()
    )

    if not letter:
        return jsonify({
            "success": False,
            "message": "Letter not found."
        }), 404

    return jsonify({
        "success": True,
        "letter": letter_to_dict(letter),
    }), 200


# ============================================================
# CREATE LETTER
# ============================================================

@letters_bp.route(
    "",
    methods=["POST"]
)
@jwt_required()
def create_letter():

    couple_id = get_user_couple_id()

    if not couple_id:
        return jsonify({
            "success": False,
            "message": "User is not connected to a couple."
        }), 403

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data provided."
        }), 400

    title = data.get("title")
    content = data.get("content")

    if not title or not title.strip():
        return jsonify({
            "success": False,
            "message": "Title is required."
        }), 400

    if not content or not content.strip():
        return jsonify({
            "success": False,
            "message": "Content is required."
        }), 400

    letter = Letter(
        couple_id=couple_id,
        title=title.strip(),
        content=content.strip(),
        is_locked=bool(
            data.get(
                "is_locked",
                False
            )
        ),
    )

    db.session.add(letter)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Letter created successfully.",
        "letter": letter_to_dict(letter),
    }), 201


# ============================================================
# UPDATE LETTER
# ============================================================

@letters_bp.route(
    "/<int:letter_id>",
    methods=["PUT"]
)
@jwt_required()
def update_letter(letter_id):

    couple_id = get_user_couple_id()

    if not couple_id:
        return jsonify({
            "success": False,
            "message": "User is not connected to a couple."
        }), 403

    letter = (
        Letter.query
        .filter_by(
            id=letter_id,
            couple_id=couple_id
        )
        .first()
    )

    if not letter:
        return jsonify({
            "success": False,
            "message": "Letter not found."
        }), 404

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data provided."
        }), 400

    if "title" in data:

        title = data.get("title")

        if not title or not title.strip():
            return jsonify({
                "success": False,
                "message": "Title cannot be empty."
            }), 400

        letter.title = title.strip()

    if "content" in data:

        content = data.get("content")

        if not content or not content.strip():
            return jsonify({
                "success": False,
                "message": "Content cannot be empty."
            }), 400

        letter.content = content.strip()

    if "is_locked" in data:

        letter.is_locked = bool(
            data["is_locked"]
        )

    letter.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Letter updated successfully.",
        "letter": letter_to_dict(letter),
    }), 200


# ============================================================
# DELETE LETTER
# ============================================================

@letters_bp.route(
    "/<int:letter_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_letter(letter_id):

    couple_id = get_user_couple_id()

    if not couple_id:
        return jsonify({
            "success": False,
            "message": "User is not connected to a couple."
        }), 403

    letter = (
        Letter.query
        .filter_by(
            id=letter_id,
            couple_id=couple_id
        )
        .first()
    )

    if not letter:
        return jsonify({
            "success": False,
            "message": "Letter not found."
        }), 404

    db.session.delete(letter)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Letter deleted successfully."
    }), 200