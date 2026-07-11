from app.extensions import db
from app.models import Notification


def notify(user_id: int, title: str, body: str, icon: str = "bell") -> Notification:
    n = Notification(user_id=user_id, title=title, body=body, icon=icon)
    db.session.add(n)
    db.session.commit()
    return n
