def get_user_payload(user):
    """Convert Django user -> JWT payload"""
    return {
        "user_id": user.id,
        "username": user.username,
        "role": getattr(user, "role", "staff"),
    }
