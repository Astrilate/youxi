from app.main.error import error
from app.main.user import user
from app.main.view import view
from app import app, db


app.register_blueprint(view)
app.register_blueprint(user)
app.register_blueprint(error)


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run()
