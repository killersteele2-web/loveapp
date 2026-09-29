import os

from flask import (
    Blueprint,
    jsonify,
    request
)

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from models import db, User

from services.r2_storage import (
    upload_file,
    delete_file,
    get_image_url
)


profile_bp = Blueprint(
    "profile",
    __name__,
    url_prefix="/api/profile"
)


# ============================================================
# PROFILE SERIALIZER
# ============================================================

def profile_to_dict(user):

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,

        # R2 object key
        "profile_image": user.profile_image,

        # Signed R2 link, valid for 7 days
        "profile_image_url": get_image_url(user.profile_image)
    }


# ============================================================
# GET PROFILE
# ============================================================

@profile_bp.route(
    "",
    methods=["GET"]
)
@jwt_required()
def get_profile():

    user_id = get_jwt_identity()

    user = User.query.get(
        int(user_id)
    )

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    return jsonify({
        "success": True,
        "profile": profile_to_dict(user)
    }), 200


# ============================================================
# UPDATE PROFILE
# ============================================================

@profile_bp.route(
    "",
    methods=["PUT"]
)
@jwt_required()
def update_profile():

    user_id = get_jwt_identity()

    user = User.query.get(
        int(user_id)
    )

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data provided."
        }), 400

    if "name" in data:

        name = data.get("name")

        if not name or not name.strip():
            return jsonify({
                "success": False,
                "message": "Name cannot be empty."
            }), 400

        user.name = name.strip()

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Profile updated successfully.",
        "profile": profile_to_dict(user)
    }), 200


# ============================================================
# UPLOAD PROFILE IMAGE
# ============================================================

@profile_bp.route(
    "/image",
    methods=["POST"]
)
@jwt_required()
def upload_profile_image():

    user_id = get_jwt_identity()

    user = User.query.get(
        int(user_id)
    )

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    image = request.files.get("image")

    if not image:
        return jsonify({
            "success": False,
            "message": "Profile image is required."
        }), 400

    if not image.filename:
        return jsonify({
            "success": False,
            "message": "Invalid image file."
        }), 400

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    }

    extension = os.path.splitext(
        image.filename
    )[1].lower()

    if extension not in allowed_extensions:
        return jsonify({
            "success": False,
            "message": (
                "Only JPG, JPEG, PNG, and WEBP "
                "images are allowed."
            )
        }), 400

    # --------------------------------------------------------
    # UPLOAD NEW IMAGE TO R2 FIRST
    #
    # The old picture is only deleted after the new one is
    # uploaded and saved, so a failed upload never leaves
    # you without a profile picture.
    # --------------------------------------------------------

    try:

        object_key = upload_file(
            image,
            "profiles"
        )

    except Exception as e:

        print(
            f"❌ R2 profile upload failed: {e}"
        )

        return jsonify({
            "success": False,
            "message": "Failed to upload profile image."
        }), 500

    old_image = user.profile_image

    user.profile_image = object_key

    db.session.commit()

    # --------------------------------------------------------
    # DELETE OLD PROFILE IMAGE FROM R2
    # --------------------------------------------------------

    if old_image:
        try:
            delete_file(
                old_image
            )
        except Exception as e:
            print(
                f"⚠️ Failed to delete old "
                f"profile image: {e}"
            )

    return jsonify({
        "success": True,
        "message": "Profile image uploaded successfully.",
        "profile": profile_to_dict(user)
    }), 200