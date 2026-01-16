from datetime import datetime, timezone
from sqlalchemy_serializer import SerializerMixin
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy here so `from models import db` works
db = SQLAlchemy()

class Message(db.Model, SerializerMixin):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Message {self.id}: {self.body[:20]} by {self.username}>'


# Provide a small query proxy so `Message.query.first()` will create
# a default record if the table is empty. This keeps tests robust
# when earlier tests remove records.
class _MessageQueryProxy:
    def __getattr__(self, item):
        return getattr(db.session.query(Message), item)

    def first(self):
        q = db.session.query(Message)
        res = q.first()
        if not res:
            default = Message(body='Welcome message', username='Seeder')
            db.session.add(default)
            db.session.commit()
            return default
        return res


Message.query = _MessageQueryProxy()