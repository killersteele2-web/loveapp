from datetime import datetime

from flask import (
    Blueprint,
    jsonify,
    request
)

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from models import (
    db,
    TimelineEvent,
    CoupleMember
)

from services.r2_storage import (
    upload_file,
    delete_file
)


timeline_bp = Blueprint(
    "timeline",
    __name__,
    url_prefix="/api/timeline"
)


# ============================================================
# GET CURRENT USER'S COUPLE
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
# SERIALIZE TIMELINE EVENT
# ============================================================

def timeline_to_dict(event):

    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "event_date": (
            event.event_date.isoformat()
            if event.event_date
            else None
        ),
        "image_path": event.image_path,
        "created_at": (
            event.created_at.isoformat()
            if event.created_at
            else None
        ),
    }


# ============================================================
# GET ALL TIMELINE EVENTS
# ============================================================

@timeline_bp.route(
    "",
    methods=["GET"]
)
@jwt_required()
def get_timeline():

    couple_id = get_user_couple_id()

    if not couple_id:
        return jsonify({
            "success": False,
            "message": "User is not connected to a couple."
        }), 403

    events = (
        TimelineEvent.query
        .filter_by(
            couple_id=couple_id
        )
        .order_by(
            TimelineEvent.event_date.asc()
        )
        .all()
    )

    return jsonify({
        "success": True,
        "events": [
            timeline_to_dict(event)
            for event in events
        ]
    }), 200


# ============================================================
# GET ONE TIMELINE EVENT
# ============================================================

@timeline_bp.route(
    "/<int:event_id>",
    methods=["GET"]
)
@jwt_required()
def get_event(event_id):

    couple_id = get_user_couple_id()

    if not couple_id:
        return jsonify({
            "success": False,
            "message": "User is not connected to a couple."
        }), 403

    event = (
        TimelineEvent.query
        .filter_by(
            id=event_id,
            couple_id=couple_id
        )
        .first()
    )

    if not event:
        return jsonify({
            "success": False,
            "message": "Timeline event not found."
        }), 404

    return jsonify({
        "success": True,
        "event": timeline_to_dict(event)
    }), 200


# ============================================================
# CREATE TIMELINE EVENT
# ============================================================

@timeline_bp.route(
    "",
    methods=["POST"]
)
@jwt_required()
def create_event():

    couple_id = get_user_couple_id()

    if not couple_id:
        return jsonify({
            "success": False,
            "message": "User is not connected to a couple."
        }), 403

    title = request.form.get(
        "title",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    event_date = request.form.get(
        "event_date"
    )

    if not title:
        return jsonify({
            "success": False,
            "message": "Title is required."
        }), 400

    if not event_date:
        return jsonify({
            "success": False,
            "message": "Event date is required."
        }), 400

    try:

        parsed_date = datetime.fromisoformat(
            event_date
        )

    except ValueError:

        return jsonify({
            "success": False,
            "message": "Invalid event date."
        }), 400

    image_path = None

    image = request.files.get(
        "image"
    )

    # --------------------------------------------------------
    # UPLOAD IMAGE TO R2
    # --------------------------------------------------------

    if image and image.filename:

        try:

            image_path = upload_file(
                image,
                "timeline"
            )

        except Exception as e:

            print(
                f"❌ R2 timeline upload failed: {e}"
            )

            return jsonify({
                "success": False,
                "message": (
                    "Failed to upload "
                    "timeline image."
                )
            }), 500

    # --------------------------------------------------------
    # CREATE DATABASE RECORD
    # --------------------------------------------------------

    event = TimelineEvent(
        couple_id=couple_id,
        title=title,
        description=description,
        event_date=parsed_date,
        image_path=image_path
    )

    db.session.add(event)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": (
            "Timeline event created successfully."
        ),
        "event": timeline_to_dict(event)
    }), 201


# ============================================================
# UPDATE TIMELINE EVENT
# ============================================================

@timeline_bp.route(
    "/<int:event_id>",
    methods=["PUT"]
)
@jwt_required()
def update_event(event_id):

    couple_id = get_user_couple_id()

    if not couple_id:
        return jsonify({
            "success": False,
            "message": "User is not connected to a couple."
        }), 403

    event = (
        TimelineEvent.query
        .filter_by(
            id=event_id,
            couple_id=couple_id
        )
        .first()
    )

    if not event:
        return jsonify({
            "success": False,
            "message": "Timeline event not found."
        }), 404

    title = request.form.get(
        "title"
    )

    description = request.form.get(
        "description"
    )

    event_date = request.form.get(
        "event_date"
    )

    if title is not None:

        title = title.strip()

        if not title:
            return jsonify({
                "success": False,
                "message": "Title cannot be empty."
            }), 400

        event.title = title

    if description is not None:

        event.description = (
            description.strip()
        )

    if event_date:

        try:

            event.event_date = (
                datetime.fromisoformat(
                    event_date
                )
            )

        except ValueError:

            return jsonify({
                "success": False,
                "message": "Invalid event date."
            }), 400

    image = request.files.get(
        "image"
    )

    # --------------------------------------------------------
    # REPLACE IMAGE IN R2
    # --------------------------------------------------------

    if image and image.filename:

        # Delete old R2 image
        if event.image_path:

            try:

                delete_file(
                    event.image_path
                )

            except Exception as e:

                print(
                    f"⚠️ Failed to delete old "
                    f"timeline image: {e}"
                )

        # Upload new R2 image
        try:

            event.image_path = upload_file(
                image,
                "timeline"
            )

        except Exception as e:

            print(
                f"❌ R2 timeline upload failed: {e}"
            )

            return jsonify({
                "success": False,
                "message": (
                    "Failed to upload "
                    "new timeline image."
                )
            }), 500

    event.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "success": True,
        "message": (
            "Timeline event updated successfully."
        ),
        "event": timeline_to_dict(event)
    }), 200


# ============================================================
# DELETE TIMELINE EVENT
# ============================================================

@timeline_bp.route(
    "/<int:event_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_event(event_id):

    couple_id = get_user_couple_id()

    if not couple_id:
        return jsonify({
            "success": False,
            "message": "User is not connected to a couple."
        }), 403

    event = (
        TimelineEvent.query
        .filter_by(
            id=event_id,
            couple_id=couple_id
        )
        .first()
    )

    if not event:
        return jsonify({
            "success": False,
            "message": "Timeline event not found."
        }), 404

    # --------------------------------------------------------
    # DELETE IMAGE FROM R2
    # --------------------------------------------------------

    if event.image_path:

        try:

            delete_file(
                event.image_path
            )

        except Exception as e:

            print(
                f"⚠️ Failed to delete "
                f"timeline image from R2: {e}"
            )

    # --------------------------------------------------------
    # DELETE DATABASE RECORD
    # --------------------------------------------------------

    db.session.delete(event)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": (
            "Timeline event deleted successfully."
        )
    }), 200