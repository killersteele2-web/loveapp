import os
from datetime import date

from flask import (
    Blueprint,
    jsonify,
    request
)

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from werkzeug.utils import secure_filename

from models import db, Memory, CoupleMember

from services.r2_storage import (
    upload_file,
    delete_file
)


memories_bp = Blueprint(
    "memories",
    __name__,
    url_prefix="/api/memories"
)


# ============================================================
# CONFIGURATION
# ============================================================

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
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
# SERIALIZE MEMORY
# ============================================================

def memory_to_dict(memory):

    return {
        "id": memory.id,
        "title": memory.title,
        "description": memory.description,
        "image_path": memory.image_path,

        "memory_date": (
            memory.memory_date.isoformat()
            if memory.memory_date
            else None
        ),

        "is_favorite": memory.is_favorite,

        "created_at": (
            memory.created_at.isoformat()
            if memory.created_at
            else None
        ),

        "updated_at": (
            memory.updated_at.isoformat()
            if memory.updated_at
            else None
        ),
    }


# ============================================================
# GET ALL MEMORIES
# ============================================================

@memories_bp.route("", methods=["GET"])
@jwt_required()
def get_memories():

    couple_id = get_user_couple_id()

    if not couple_id:
        return jsonify({
            "success": False,
            "message": "User is not connected to a couple."
        }), 403

    memories = (
        Memory.query
        .filter_by(couple_id=couple_id)
        .order_by(
            Memory.memory_date.desc(),
            Memory.created_at.desc()
        )
        .all()
    )

    return jsonify({
        "success": True,
        "memories": [
            memory_to_dict(memory)
            for memory in memories
        ]
    })


# ============================================================
# GET SINGLE MEMORY
# ============================================================

@memories_bp.route(
    "/<int:memory_id>",
    methods=["GET"]
)
@jwt_required()
def get_memory(memory_id):

    couple_id = get_user_couple_id()

    if not couple_id:
        return jsonify({
            "success": False,
            "message": "User is not connected to a couple."
        }), 403

    memory = (
        Memory.query
        .filter_by(
            id=memory_id,
            couple_id=couple_id
        )
        .first()
    )

    if not memory:
        return jsonify({
            "success": False,
            "message": "Memory not found."
        }), 404

    return jsonify({
        "success": True,
        "memory": memory_to_dict(memory)
    })


# ============================================================
# CREATE MEMORY
# ============================================================

@memories_bp.route("", methods=["POST"])
@jwt_required()
def create_memory():

    couple_id = get_user_couple_id()

    if not couple_id:
        return jsonify({
            "success": False,
            "message": "User is not connected to a couple."
        }), 403

    title = request.form.get("title")

    if not title:
        return jsonify({
            "success": False,
            "message": "Title is required"
        }), 400

    description = request.form.get("description")
    memory_date = request.form.get("memory_date")

    parsed_date = None

    if memory_date:

        try:
            parsed_date = date.fromisoformat(
                memory_date
            )

        except ValueError:

            return jsonify({
                "success": False,
                "message": "Invalid date. Use YYYY-MM-DD."
            }), 400

    image_path = None

    # --------------------------------------------------------
    # IMAGE UPLOAD TO R2
    # --------------------------------------------------------

    if "image" in request.files:

        image = request.files["image"]

        if image.filename:

            if not allowed_file(image.filename):

                return jsonify({
                    "success": False,
                    "message": "Unsupported image format"
                }), 400

            try:

                image_path = upload_file(
                    image,
                    "memories"
                )

            except Exception as e:

                print(
                    f"❌ R2 memory upload failed: {e}"
                )

                return jsonify({
                    "success": False,
                    "message": "Failed to upload memory image."
                }), 500

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    memory = Memory(
        couple_id=couple_id,
        title=title,
        description=description,
        memory_date=parsed_date,
        image_path=image_path,
        is_favorite=False
    )

    db.session.add(memory)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Memory created successfully ❤️",
        "memory": memory_to_dict(memory)
    }), 201


# ============================================================
# UPDATE MEMORY
# ============================================================

@memories_bp.route(
    "/<int:memory_id>",
    methods=["PUT"]
)
@jwt_required()
def update_memory(memory_id):

    couple_id = get_user_couple_id()

    if not couple_id:
        return jsonify({
            "success": False,
            "message": "User is not connected to a couple."
        }), 403

    memory = (
        Memory.query
        .filter_by(
            id=memory_id,
            couple_id=couple_id
        )
        .first()
    )

    if not memory:

        return jsonify({
            "success": False,
            "message": "Memory not found"
        }), 404

    data = request.form

    if "title" in data:

        title = data.get("title")

        if title:
            memory.title = title

    if "description" in data:

        memory.description = data.get(
            "description"
        )

    if "memory_date" in data:

        memory_date = data.get(
            "memory_date"
        )

        if memory_date:

            try:

                memory.memory_date = (
                    date.fromisoformat(
                        memory_date
                    )
                )

            except ValueError:

                return jsonify({
                    "success": False,
                    "message": (
                        "Invalid date. "
                        "Use YYYY-MM-DD."
                    )
                }), 400

    # --------------------------------------------------------
    # UPDATE IMAGE IN R2
    # --------------------------------------------------------

    if "image" in request.files:

        image = request.files["image"]

        if image.filename:

            if not allowed_file(
                image.filename
            ):

                return jsonify({
                    "success": False,
                    "message": (
                        "Unsupported image format"
                    )
                }), 400

            # Delete old R2 image
            if memory.image_path:

                try:

                    delete_file(
                        memory.image_path
                    )

                except Exception as e:

                    print(
                        f"⚠️ Failed to delete old "
                        f"memory image: {e}"
                    )

            # Upload new R2 image
            try:

                image_path = upload_file(
                    image,
                    "memories"
                )

                memory.image_path = image_path

            except Exception as e:

                print(
                    f"❌ R2 memory upload failed: {e}"
                )

                return jsonify({
                    "success": False,
                    "message": (
                        "Failed to upload "
                        "new memory image."
                    )
                }), 500

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Memory updated successfully ❤️",
        "memory": memory_to_dict(memory)
    })


# ============================================================
# FAVORITE / UNFAVORITE
# ============================================================

@memories_bp.route(
    "/<int:memory_id>/favorite",
    methods=["PATCH"]
)
@jwt_required()
def toggle_favorite(memory_id):

    couple_id = get_user_couple_id()

    if not couple_id:
        return jsonify({
            "success": False,
            "message": "User is not connected to a couple."
        }), 403

    memory = (
        Memory.query
        .filter_by(
            id=memory_id,
            couple_id=couple_id
        )
        .first()
    )

    if not memory:

        return jsonify({
            "success": False,
            "message": "Memory not found"
        }), 404

    memory.is_favorite = (
        not memory.is_favorite
    )

    db.session.commit()

    return jsonify({
        "success": True,
        "is_favorite": memory.is_favorite,
        "memory": memory_to_dict(memory)
    })


# ============================================================
# DELETE MEMORY
# ============================================================

@memories_bp.route(
    "/<int:memory_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_memory(memory_id):

    couple_id = get_user_couple_id()

    if not couple_id:
        return jsonify({
            "success": False,
            "message": "User is not connected to a couple."
        }), 403

    memory = (
        Memory.query
        .filter_by(
            id=memory_id,
            couple_id=couple_id
        )
        .first()
    )

    if not memory:

        return jsonify({
            "success": False,
            "message": "Memory not found"
        }), 404

    # --------------------------------------------------------
    # DELETE IMAGE FROM R2
    # --------------------------------------------------------

    if memory.image_path:

        try:

            delete_file(
                memory.image_path
            )

        except Exception as e:

            print(
                f"⚠️ Failed to delete "
                f"memory image from R2: {e}"
            )

    # --------------------------------------------------------
    # DELETE DATABASE RECORD
    # --------------------------------------------------------

    db.session.delete(memory)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": (
            "Memory deleted successfully ❤️"
        )
    })


# ============================================================
# OLD LOCAL IMAGE ROUTE REMOVED
# ============================================================
#
# Images are now stored in Cloudflare R2.
#
# The old:
#
# /api/memories/image/<filename>
#
# endpoint is intentionally removed.
#
# Flutter should eventually receive a proper R2
# image URL or signed URL.
#