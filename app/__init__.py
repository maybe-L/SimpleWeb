from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask import send_from_directory


import os

import logging
from logging.handlers import RotatingFileHandler




csrf = CSRFProtect()

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    csrf.init_app(app)

    app.config['SECRET_KEY'] = 'your_secret_key_here'  # 비밀 키 설정
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://maybee:1234@localhost:5432/maybeedb'
        # 파일 업로드 폴더 설정
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])


    # 로깅 설정
    if not app.debug:
        file_handler = RotatingFileHandler('error.log', maxBytes=10240, backupCount=10)
        file_handler.setLevel(logging.ERROR)
        app.logger.addHandler(file_handler)

    # CSRF 보호 활성화

    # db 초기화
    db.init_app(app)
    migrate.init_app(app, db)

    # Flask-Login 초기화
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'  # 로그인 뷰 설정

    # 사용자 로드 함수
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 모델 임포트
    from .models import User

    # 라우트 임포트
    from .routes import bp as main_bp  # 블루프린트 다시 'main'으로 임포트
    app.register_blueprint(main_bp)  # URL 프리픽스 없이 등록

    # dist 폴더 내의 파일을 서빙할 수 있도록 경로 설정
    @app.route('/dist/<path:filename>')
    def dist_static(filename):
        return send_from_directory('dist', filename)




    return app
