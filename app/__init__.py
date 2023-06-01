from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from redis.client import StrictRedis

from app import config

SECRET_KEY = "asjcklqencoiwrev45y6"

app = Flask(__name__, static_folder='D:/Users/asus/Desktop/youxi/static')

CORS(app, supports_credentials=True)

app.config.from_object(config)
app.config['SECRET_KEY'] = SECRET_KEY

redis_store = StrictRedis(host="127.0.0.1", port=6379, decode_responses=True)

db = SQLAlchemy(app)
