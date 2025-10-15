from sqlalchemy.orm import Session
from entity.user_entity import Notification


def get_template_body(db: Session, client_id: str, template_name: str, notif_type: str = "template"):
    template_from_db = (
        db.query(Notification)
        .filter_by(client_id=client_id, template_name=template_name, type=notif_type)
        .first()
    )
    return template_from_db.template_body if template_from_db else None



def render_template(template_body: str, metadata: dict):    
    try:
        return template_body.format(**metadata)
    except KeyError:
        return template_body
