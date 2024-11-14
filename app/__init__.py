# __init__.py 내용
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask import send_from_directory
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

csrf = CSRFProtect()
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    csrf.init_app(app)
    load_dotenv()
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///default.db')
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['THUMBNAIL_FOLDER'] = os.path.join(app.root_path, 'static', 'thumbnails')

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['THUMBNAIL_FOLDER']):
        os.makedirs(app.config['THUMBNAIL_FOLDER'])
        app.logger.info(f'Thumbnail folder created at {app.config["THUMBNAIL_FOLDER"]}')

    if not app.debug:
        file_handler = RotatingFileHandler('error.log', maxBytes=10240, backupCount=10)
        file_handler.setLevel(logging.ERROR)
        app.logger.addHandler(file_handler)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .models import User
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app

app = create_app()  # 전역 app 객체 생성