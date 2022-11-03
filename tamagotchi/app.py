from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .utils import required_env

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{app.instance_path}/db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = required_env("FLASK_SECRET_KEY")
db = SQLAlchemy(app)
