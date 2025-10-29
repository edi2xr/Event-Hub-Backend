from flask import Blueprint, jsonify, request
from extensions import db
from models.user import User
from models.club import Club
from models.event import Event
from models.notification import Notification
from models.audit import AuditLog
from utils.decorators import token_required, admin_only

admin_bp = Blueprint("admin", __name__)

# ==============================================
# DASHBOARD
# ==============================================
@admin_bp.route("/dashboard", methods=["GET"])
@token_required
@admin_only
def admin_dashboard(current_user):
    """Show a quick summary of total users, clubs, and events."""
    stats = {
        "users": User.query.count(),
        "clubs": Club.query.count(),
        "events": Event.query.count(),
        "pending_events": Event.query.filter_by(status="pending").count()
    }

    return jsonify({
        "message": f"Welcome, {current_user.full_name}",
        "stats": stats
    }), 200


# ==============================================
# USER MANAGEMENT
# ==============================================
@admin_bp.route("/users", methods=["GET"])
@token_required
@admin_only
def get_all_users(current_user):
    """Return a list of all registered users."""
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200


@admin_bp.route("/users/<int:user_id>/role", methods=["PATCH"])
@token_required
@admin_only
def update_user_role(current_user, user_id):
    """Change a user's role (admin, leader, or user)."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    new_role = data.get("role")
    if new_role not in ["admin", "leader", "user"]:
        return jsonify({"error": "Invalid role"}), 400

    user.role = new_role
    db.session.commit()

    AuditLog.log_action(
        user_id=current_user.id,
        action="update",
        target_table="users",
        target_id=user.id,
        description=f"Changed {user.full_name}'s role to {new_role}"
    )
    db.session.commit()

    return jsonify({"message": f"{user.full_name}'s role updated to {new_role}"}), 200


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@token_required
@admin_only
def delete_user(current_user, user_id):
    """Remove a user account permanently."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()

    AuditLog.log_action(
        user_id=current_user.id,
        action="delete",
        target_table="users",
        target_id=user_id,
        description=f"Deleted user ID {user_id}"
    )
    db.session.commit()

    return jsonify({"message": f"User {user_id} deleted successfully"}), 200


# ==============================================
# CLUB MANAGEMENT
# ==============================================
@admin_bp.route("/clubs", methods=["GET"])
@token_required
@admin_only
def list_clubs(current_user):
    """Return all clubs."""
    clubs = Club.query.all()
    return jsonify([c.to_dict() for c in clubs]), 200


@admin_bp.route("/clubs", methods=["POST"])
@token_required
@admin_only
def create_club(current_user):
    """Create a new club."""
    data = request.get_json()
    name = data.get("name")

    if not name:
        return jsonify({"error": "Club name required"}), 400

    new_club = Club(name=name, description=data.get("description"))
    db.session.add(new_club)
    db.session.commit()

    AuditLog.log_action(
        user_id=current_user.id,
        action="create",
        target_table="clubs",
        target_id=new_club.id,
        description=f"Created club '{name}'"
    )
    db.session.commit()

    return jsonify({"message": "Club created successfully", "club": new_club.to_dict()}), 201


@admin_bp.route("/clubs/<int:club_id>", methods=["DELETE"])
@token_required
@admin_only
def delete_club(current_user, club_id):
    """Delete a club."""
    club = Club.query.get(club_id)
    if not club:
        return jsonify({"error": "Club not found"}), 404

    db.session.delete(club)
    db.session.commit()

    AuditLog.log_action(
        user_id=current_user.id,
        action="delete",
        target_table="clubs",
        target_id=club_id,
        description=f"Deleted club ID {club_id}"
    )
    db.session.commit()

    return jsonify({"message": f"Club {club_id} deleted successfully"}), 200


# ==============================================
# EVENT APPROVALS
# ==============================================
@admin_bp.route("/events/pending", methods=["GET"])
@token_required
@admin_only
def list_pending_events(current_user):
    """List all pending events waiting for approval."""
    events = Event.query.filter_by(status="pending").all()
    return jsonify([e.to_dict() for e in events]), 200


@admin_bp.route("/events/<int:event_id>/approve", methods=["PATCH"])
@token_required
@admin_only
def approve_event(current_user, event_id):
    """Approve an event request."""
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    event.status = "approved"
    db.session.commit()

    Notification.create(
        user_id=event.created_by,
        message=f"Your event '{event.title}' has been approved."
    )
    AuditLog.log_action(
        user_id=current_user.id,
        action="approve",
        target_table="events",
        target_id=event_id,
        description=f"Approved event '{event.title}'"
    )
    db.session.commit()

    return jsonify({"message": f"Event '{event.title}' approved"}), 200


@admin_bp.route("/events/<int:event_id>/reject", methods=["PATCH"])
@token_required
@admin_only
def reject_event(current_user, event_id):
    """Reject an event request."""
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    event.status = "rejected"
    db.session.commit()

    Notification.create(
        user_id=event.created_by,
        message=f"Your event '{event.title}' has been rejected."
    )
    AuditLog.log_action(
        user_id=current_user.id,
        action="reject",
        target_table="events",
        target_id=event_id,
        description=f"Rejected event '{event.title}'"
    )
    db.session.commit()

    return jsonify({"message": f"Event '{event.title}' rejected"}), 200


# ==============================================
# NOTIFICATIONS (ADMIN → USERS/LEADERS)
# ==============================================
@admin_bp.route("/notify", methods=["POST"])
@token_required
@admin_only
def send_notification(current_user):
    """Send a message to a user."""
    data = request.get_json()
    message = data.get("message")
    user_id = data.get("user_id")

    if not message or not user_id:
        return jsonify({"error": "Message and user_id are required"}), 400

    notif = Notification.create(
        user_id=user_id,
        message=f"Admin message: {message}"
    )

    AuditLog.log_action(
        user_id=current_user.id,
        action="notify",
        target_table="notifications",
        target_id=notif.id,
        description=f"Sent notification to user ID {user_id}"
    )
    db.session.commit()

    return jsonify({"message": "Notification sent successfully"}), 201


# ==============================================
# TEST ROUTE
# ==============================================
@admin_bp.route("/test", methods=["GET"])
def test_route():
    return jsonify({"message": "Admin routes working fine ✅"}), 200
