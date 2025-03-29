def db_status_from_ui(status_ui: str) -> str:
    """Convert the user-facing status to the DB value."""
    if status_ui == "Ready to Deliver":
        return "Return"
    return status_ui

def ui_status_from_db(status_db: str) -> str:
    """Convert the DB status to the user-facing label."""
    if status_db == "Return":
        return "Ready to Deliver"
    return status_db
