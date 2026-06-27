from sqlalchemy.orm import Session

from models import AdminAuditLog, User


def log_admin_action(
    db: Session,
    admin: User,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    details: str | None = None,
) -> None:
    db.add(
        AdminAuditLog(
            admin_user_id=admin.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
    )
