from flask import Flask
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_cors import CORS
from database import init_db
from auth.routes import auth_bp
from resumes.routes import resume_bp
from config import Config   
from resumes.mailer import init_mail

app = Flask(__name__)
app.config.from_object(Config)
app.config["SECRET_KEY"] = Config.SECRET_KEY


CORS(app)
JWTManager(app)
init_db(app)
init_mail(app)

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(resume_bp, url_prefix="/resumes")

if __name__ == "__main__":
    app.run(debug=True)
