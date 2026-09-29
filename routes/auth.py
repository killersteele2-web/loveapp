from flask import Blueprint, jsonify, request

from flask_bcrypt import Bcrypt

from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)

from models import (
    db,
    User,
    Couple,
    CoupleMember
)

from services.r2_storage import get_image_url


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth"
)

bcrypt = Bcrypt()


# ============================================================
# HELPERS
# ============================================================

def serialize_user(user):
    """User JSON with both the stored R2 key and a usable link."""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "profile_image": user.profile_image,
        "profile_image_url": get_image_url(user.profile_image)
    }


# ============================================================
# REGISTER
# ============================================================

@auth_bp.route(
    "/register",
    methods=["POST"]
)
def register():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required."
        }), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if not name:
        return jsonify({
            "success": False,
            "message": "Name is required."
        }), 400

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400

    if not password:
        return jsonify({
            "success": False,
            "message": "Password is required."
        }), 400

    if len(password) < 8:
        return jsonify({
            "success": False,
            "message": "Password must be at least 8 characters."
        }), 400

    # --------------------------------------------------------
    # Check existing account
    # --------------------------------------------------------

    existing_user = User.query.filter_by(
        email=email
    ).first()

    if existing_user:
        return jsonify({
            "success": False,
            "message": "An account with this email already exists."
        }), 409

    # --------------------------------------------------------
    # Hash password
    # --------------------------------------------------------

    password_hash = bcrypt.generate_password_hash(
        password
    ).decode("utf-8")

    # --------------------------------------------------------
    # Create user
    # --------------------------------------------------------

    user = User(
        name=name,
        email=email,
        password_hash=password_hash
    )

    db.session.add(user)
    db.session.flush()

    # --------------------------------------------------------
    # Create a new couple
    # --------------------------------------------------------

    couple = Couple(
        invite_code=Couple.generate_invite_code()
    )

    db.session.add(couple)
    db.session.flush()

    # --------------------------------------------------------
    # Add user as first couple member
    # --------------------------------------------------------

    membership = CoupleMember(
        couple_id=couple.id,
        user_id=user.id
    )

    db.session.add(membership)

    # --------------------------------------------------------
    # Save everything
    # --------------------------------------------------------

    db.session.commit()

    # --------------------------------------------------------
    # Create JWT
    # --------------------------------------------------------

    access_token = create_access_token(
        identity=str(user.id)
    )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return jsonify({
        "success": True,
        "message": "Account created successfully.",
        "token": access_token,
        "user": serialize_user(user),
        "couple": {
            "id": couple.id,
            "invite_code": couple.invite_code,
            "relationship_start_date": (
                couple.relationship_start_date.isoformat()
                if couple.relationship_start_date
                else None
            )
        }
    }), 201


# ============================================================
# LOGIN
# ============================================================

@auth_bp.route(
    "/login",
    methods=["POST"]
)
def login():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required."
        }), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400

    if not password:
        return jsonify({
            "success": False,
            "message": "Password is required."
        }), 400

    # --------------------------------------------------------
    # Find user
    # --------------------------------------------------------

    user = User.query.filter_by(
        email=email
    ).first()

    if not user:
        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    # --------------------------------------------------------
    # Check password
    # --------------------------------------------------------

    password_valid = bcrypt.check_password_hash(
        user.password_hash,
        password
    )

    if not password_valid:
        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    # --------------------------------------------------------
    # Find couple membership
    # --------------------------------------------------------

    membership = CoupleMember.query.filter_by(
        user_id=user.id
    ).first()

    couple_id = None
    invite_code = None

    if membership:

        couple_id = membership.couple_id

        couple = Couple.query.get(
            membership.couple_id
        )

        if couple:
            invite_code = couple.invite_code

    # --------------------------------------------------------
    # Create JWT
    # --------------------------------------------------------

    access_token = create_access_token(
        identity=str(user.id)
    )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "token": access_token,
        "user": serialize_user(user),
        "couple": {
            "id": couple_id,
            "invite_code": invite_code
        }
    }), 200


# ============================================================
# CURRENT USER
# ============================================================

@auth_bp.route(
    "/me",
    methods=["GET"]
)
@jwt_required()
def me():

    # --------------------------------------------------------
    # Get user ID from JWT
    # --------------------------------------------------------

    user_id = get_jwt_identity()

    # --------------------------------------------------------
    # Find user
    # --------------------------------------------------------

    user = User.query.get(
        int(user_id)
    )

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    # --------------------------------------------------------
    # Find couple membership
    # --------------------------------------------------------

    membership = CoupleMember.query.filter_by(
        user_id=user.id
    ).first()

    couple_id = None
    invite_code = None
    relationship_start_date = None
    partner = None

    if membership:

        couple_id = membership.couple_id

        couple = Couple.query.get(
            membership.couple_id
        )

        if couple:

            invite_code = couple.invite_code

            relationship_start_date = (
                couple.relationship_start_date.isoformat()
                if couple.relationship_start_date
                else None
            )

            # ------------------------------------------------
            # Find the other member of the couple
            # ------------------------------------------------

            for member in couple.members:

                if member.user_id != user.id:

                    partner_user = member.user

                    if partner_user:
                        partner = serialize_user(partner_user)

                    break

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return jsonify({
        "success": True,
        "user": serialize_user(user),
        "partner": partner,
        "couple": {
            "id": couple_id,
            "invite_code": invite_code,
            "relationship_start_date": relationship_start_date
        }
    }), 200