from flask import Blueprint, jsonify, request

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from models import (
    db,
    User,
    Couple,
    CoupleMember,
    Memory,
    Letter,
    TimelineEvent
)

from datetime import datetime

couples_bp = Blueprint(
    "couples",
    __name__,
    url_prefix="/api/couples"
)


# ============================================================
# HELPERS
# ============================================================

def get_current_user():
    user_id = get_jwt_identity()

    return User.query.get(
        int(user_id)
    )


def get_current_membership(user_id):
    return CoupleMember.query.filter_by(
        user_id=user_id
    ).first()


def serialize_member(user):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "profile_image": user.profile_image
    }


def serialize_couple(couple):
    members = []

    for member in couple.members:
        if member.user:
            members.append(
                serialize_member(member.user)
            )

    return {
        "id": couple.id,
        "invite_code": couple.invite_code,
        "relationship_start_date": (
            couple.relationship_start_date.isoformat()
            if couple.relationship_start_date
            else None
        ),
        "members": members
    }


# ============================================================
# GET MY COUPLE
# ============================================================

@couples_bp.route(
    "/me",
    methods=["GET"]
)
@jwt_required()
def get_my_couple():

    user = get_current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    membership = get_current_membership(
        user.id
    )

    if not membership:
        return jsonify({
            "success": False,
            "message": "You are not connected to a couple."
        }), 404

    couple = Couple.query.get(
        membership.couple_id
    )

    if not couple:
        return jsonify({
            "success": False,
            "message": "Couple not found."
        }), 404

    return jsonify({
        "success": True,
        "couple": serialize_couple(couple)
    }), 200

# ============================================================
# UPDATE RELATIONSHIP DATE
# ============================================================

@couples_bp.route(
    "/me/relationship-date",
    methods=["PUT"]
)
@jwt_required()
def update_relationship_date():

    user = get_current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    membership = get_current_membership(
        user.id
    )

    if not membership:
        return jsonify({
            "success": False,
            "message": (
                "You are not connected to a couple."
            )
        }), 404

    couple = Couple.query.get(
        membership.couple_id
    )

    if not couple:
        return jsonify({
            "success": False,
            "message": "Couple not found."
        }), 404

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required."
        }), 400

    date_value = data.get(
        "relationship_start_date"
    )

    # --------------------------------------------------------
    # CLEAR DATE
    # --------------------------------------------------------

    if date_value is None or str(date_value).strip() == "":
        couple.relationship_start_date = None

    # --------------------------------------------------------
    # SET DATE
    # --------------------------------------------------------

    else:
        try:
            couple.relationship_start_date = (
                datetime.strptime(
                    str(date_value).strip(),
                    "%Y-%m-%d"
                ).date()
            )

        except ValueError:
            return jsonify({
                "success": False,
                "message": (
                    "Invalid relationship date. "
                    "Use YYYY-MM-DD."
                )
            }), 400

    db.session.commit()

    return jsonify({
        "success": True,
        "message": (
            "Relationship date updated successfully."
        ),
        "couple": serialize_couple(couple)
    }), 200

# ============================================================
# JOIN COUPLE
# ============================================================

@couples_bp.route(
    "/join",
    methods=["POST"]
)
@jwt_required()
def join_couple():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required."
        }), 400

    invite_code = data.get(
        "invite_code",
        ""
    ).strip().upper()

    if not invite_code:
        return jsonify({
            "success": False,
            "message": "Invite code is required."
        }), 400

    # --------------------------------------------------------
    # CURRENT USER
    # --------------------------------------------------------

    user = get_current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    # --------------------------------------------------------
    # FIND TARGET COUPLE
    # --------------------------------------------------------

    target_couple = Couple.query.filter_by(
        invite_code=invite_code
    ).first()

    if not target_couple:
        return jsonify({
            "success": False,
            "message": "Invalid invite code."
        }), 404

    # --------------------------------------------------------
    # CHECK IF ALREADY IN TARGET COUPLE
    # --------------------------------------------------------

    existing_target_membership = (
        CoupleMember.query.filter_by(
            couple_id=target_couple.id,
            user_id=user.id
        ).first()
    )

    if existing_target_membership:
        return jsonify({
            "success": False,
            "message": "You are already a member of this couple."
        }), 409

    # --------------------------------------------------------
    # MAXIMUM OF TWO MEMBERS
    # --------------------------------------------------------

    member_count = CoupleMember.query.filter_by(
        couple_id=target_couple.id
    ).count()

    if member_count >= 2:
        return jsonify({
            "success": False,
            "message": "This couple already has two members."
        }), 409

    # --------------------------------------------------------
    # CHECK CURRENT COUPLE
    # --------------------------------------------------------

    current_membership = get_current_membership(
        user.id
    )

    if current_membership:

        current_couple = Couple.query.get(
            current_membership.couple_id
        )

        if current_couple:

            # ------------------------------------------------
            # ALREADY IN TARGET COUPLE
            # ------------------------------------------------

            if current_couple.id == target_couple.id:
                return jsonify({
                    "success": False,
                    "message": "You are already in this couple."
                }), 409

            # ------------------------------------------------
            # CURRENT COUPLE DATA
            # ------------------------------------------------

            memory_count = Memory.query.filter_by(
                couple_id=current_couple.id
            ).count()

            letter_count = Letter.query.filter_by(
                couple_id=current_couple.id
            ).count()

            timeline_count = TimelineEvent.query.filter_by(
                couple_id=current_couple.id
            ).count()

            if (
                memory_count > 0
                or letter_count > 0
                or timeline_count > 0
            ):
                return jsonify({
                    "success": False,
                    "message": (
                        "You already have data in your current "
                        "couple. You cannot join another couple."
                    )
                }), 409

            # ------------------------------------------------
            # REMOVE OLD MEMBERSHIP
            # ------------------------------------------------

            db.session.delete(
                current_membership
            )

            db.session.flush()

            # ------------------------------------------------
            # DELETE OLD EMPTY COUPLE
            # ------------------------------------------------

            remaining_members = (
                CoupleMember.query.filter_by(
                    couple_id=current_couple.id
                ).count()
            )

            if remaining_members == 0:
                db.session.delete(
                    current_couple
                )

    # --------------------------------------------------------
    # CREATE NEW MEMBERSHIP
    # --------------------------------------------------------

    membership = CoupleMember(
        couple_id=target_couple.id,
        user_id=user.id
    )

    db.session.add(
        membership
    )

    db.session.commit()

    # --------------------------------------------------------
    # RETURN UPDATED COUPLE
    # --------------------------------------------------------

    return jsonify({
        "success": True,
        "message": "You joined the couple successfully.",
        "couple": serialize_couple(target_couple)
    }), 200