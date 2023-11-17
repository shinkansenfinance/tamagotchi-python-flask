from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .utils import required_env
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    if required_env("SHINKANSEN_API_HOST") == "api.shinkansen.finance":
        return username == required_env(
            "HTTP_AUTH_USERNAME"
        ) and password == required_env("HTTP_AUTH_PASSWORD")
    else:
        return True


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{app.instance_path}/db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = required_env("FLASK_SECRET_KEY")
db = SQLAlchemy(app)
