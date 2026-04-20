from models import Notification

def queue_notification(
    recipient_id,
    title,
    message,
    *,
    category='general',
    actor_id=None,
    entity_type=None,
    entity_id=None
):
    if not recipient_id:
        raise ValueError('recipient_id is required')
    if not title or not title.strip():
        raise ValueError('title is required')
    if not message or not message.strip():
        raise ValueError('message is required')
    if actor_id is not None and recipient_id == actor_id:
        return None

    notification = Notification()
    notification.recipient_id = recipient_id
    notification.actor_id = actor_id
    notification.category = category
    notification.title = title.strip()
    notification.message = message.strip()
    notification.entity_type = entity_type
    notification.entity_id = entity_id

    return notification
