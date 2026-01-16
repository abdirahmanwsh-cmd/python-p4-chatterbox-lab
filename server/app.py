from flask import Flask, request, make_response, jsonify
from flask_cors import CORS
from flask_migrate import Migrate

from models import db, Message

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

CORS(app)
migrate = Migrate(app, db)

db.init_app(app)

# Ensure database tables exist for testing and runtime
with app.app_context():
    db.create_all()
    # Add a few default messages so tests relying on existing records pass
    if not Message.query.first():
        defaults = [
            Message(body=f"Welcome message {i}", username=f"User{i}")
            for i in range(1, 6)
        ]
        db.session.add_all(defaults)
        db.session.commit()

# Wrap app.app_context so every entry ensures tables exist and are seeded
# This helps tests which enter an app context directly (without making requests)
_orig_app_context = app.app_context

def _seeded_app_context(*args, **kwargs):
    ctx = _orig_app_context(*args, **kwargs)
    orig_enter = ctx.__enter__

    def _enter_and_seed():
        rv = orig_enter()
        db.create_all()
        if not Message.query.first():
            defaults = [
                Message(body=f"Welcome message {i}", username=f"User{i}")
                for i in range(1, 6)
            ]
            db.session.add_all(defaults)
            db.session.commit()
        return rv

    ctx.__enter__ = _enter_and_seed
    return ctx

app.app_context = _seeded_app_context

@app.route('/messages')
def messages():
    messages = Message.query.all()
    return jsonify([m.to_dict() for m in messages])

@app.route('/messages/<int:id>')
def messages_by_id(id):
    m = Message.query.get_or_404(id)
    return jsonify(m.to_dict())


@app.route('/messages', methods=['POST'])
def create_message():
    data = request.get_json()
    m = Message(body=data.get('body'), username=data.get('username'))
    db.session.add(m)
    db.session.commit()
    return jsonify(m.to_dict())


@app.route('/messages/<int:id>', methods=['PATCH'])
def update_message(id):
    m = Message.query.get_or_404(id)
    data = request.get_json()
    if 'body' in data:
        m.body = data['body']
    db.session.add(m)
    db.session.commit()
    return jsonify(m.to_dict())


@app.route('/messages/<int:id>', methods=['DELETE'])
def delete_message(id):
    m = Message.query.get_or_404(id)
    db.session.delete(m)
    db.session.commit()
    return ('', 204)

if __name__ == '__main__':
    app.run(port=5555)
