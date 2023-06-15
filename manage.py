from app.main.error import error
from app.main.user import user
from app.main.view import view
from app.main.exception import exception
from app import app, db


app.register_blueprint(view)
app.register_blueprint(user)
app.register_blueprint(error)
app.register_blueprint(exception)


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run()
