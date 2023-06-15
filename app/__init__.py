from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from app import config

SECRET_KEY = "asjcklqencoiwrev45y6"

app = Flask(__name__, static_folder='D:/Users/asus/Desktop/youxi/static')

CORS(app, supports_credentials=True)

app.config.from_object(config)
app.config['SECRET_KEY'] = SECRET_KEY

db = SQLAlchemy(app)
